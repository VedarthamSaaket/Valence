import numpy as np
import os
import pickle
import threading
import time
from typing import Dict, Optional, List

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

# How long a request is willing to wait for the model to finish loading
# before falling back to the statistical assignment (seconds).
READY_WAIT_SECS = float(os.getenv("REFINER_READY_WAIT", "180"))


class ArchetypeRefiner:
    """Local-LLM archetype refinement.

    The model is loaded ONCE, in a background thread, at server startup
    (see main.py lifespan). Requests that arrive while it is still loading
    wait on the ready event instead of silently skipping enrichment, so
    results are never stamped with placeholder archetypes just because the
    model was not awake yet.
    """

    _instance = None

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._cluster_profiles_cache: Dict[str, Dict] = {}
        self._ready = threading.Event()
        self._load_lock = threading.Lock()
        self._load_started = False

    @classmethod
    def instance(cls) -> "ArchetypeRefiner":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------ load

    def warm_up(self, background: bool = True):
        """Kick off model loading. Idempotent.

        background=True returns immediately, the server keeps booting while
        the model loads in a daemon thread. Requests will wait on the ready
        event via wait_until_ready().
        """
        with self._load_lock:
            if self._load_started:
                return
            self._load_started = True

        if background:
            t = threading.Thread(target=self._load, name="refiner-warmup", daemon=True)
            t.start()
        else:
            self._load()

    def _load(self):
        t0 = time.time()
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Use every core for CPU inference.
            try:
                torch.set_num_threads(max(1, os.cpu_count() or 1))
            except Exception:
                pass

            cuda = torch.cuda.is_available()

            # Dtype choice is a correctness matter here, not just speed. On
            # some CPU builds, converting the refiner's native weights to
            # fp32 (either at load time or via a later .float()) crashes the
            # process. Loading and running in the weights' native precision
            # avoids that path: keep bf16 on CPU and never convert; use fp16
            # on GPU. Override with ARCHETYPE_REFINER_DTYPE if a host needs it.
            dtype_env = (os.getenv("ARCHETYPE_REFINER_DTYPE") or "").strip().lower()
            dtype_map = {
                "float32": torch.float32, "fp32": torch.float32,
                "float16": torch.float16, "fp16": torch.float16,
                "bfloat16": torch.bfloat16, "bf16": torch.bfloat16,
                "auto": "auto",
            }
            if dtype_env in dtype_map:
                load_dtype = dtype_map[dtype_env]
            else:
                load_dtype = torch.float16 if cuda else torch.bfloat16

            model_id = os.getenv(
                "ARCHETYPE_REFINER_ID", "Qwen/Qwen2.5-1.5B-Instruct"
            )
            self._tokenizer = AutoTokenizer.from_pretrained(model_id)
            self._model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=load_dtype,
                device_map="auto" if cuda else None,
                low_cpu_mem_usage=True,
            )
            if not cuda:
                # Move device only — do NOT change dtype (no .float()).
                self._model = self._model.to("cpu")
            self._model.eval()

            # Scrub the checkpoint's sampling defaults so greedy decoding
            # (do_sample=False) does not trigger transformers warnings about
            # temperature / top_p / top_k being set but unused.
            gc = self._model.generation_config
            gc.do_sample = False
            gc.temperature = None
            gc.top_p = None
            gc.top_k = None

            print(f"[refiner] ready in {time.time() - t0:.1f}s")
        except Exception as e:
            print(f"[refiner] unavailable: {e}")
            self._model = None
        finally:
            self._ready.set()

        # Pre-warm cluster profiles for every test so the first submit of
        # each test does not pay the matrix-load + predict cost.
        if self._model is not None:
            t1 = time.time()
            import json as _json
            for fn in os.listdir(MODELS_DIR):
                if not fn.endswith("_meta.json"):
                    continue
                test_id = fn[:-len("_meta.json")]
                try:
                    with open(os.path.join(MODELS_DIR, fn), encoding="utf-8") as f:
                        meta = _json.load(f)
                    names = meta.get("trait_names")
                    if names:
                        self._get_cluster_profiles(test_id, names)
                except Exception:
                    pass
            print(f"[refiner] cluster profiles pre-warmed in {time.time() - t1:.1f}s")

    @property
    def available(self) -> bool:
        return self._model is not None

    def wait_until_ready(self, timeout: float = READY_WAIT_SECS) -> bool:
        """Block until the model finished loading (or failed), then report
        availability. Called at the top of refine()/enrich_insights() so a
        submit that lands mid-load waits instead of skipping enrichment."""
        if not self._load_started:
            # Nothing ever started loading, start it now rather than fail.
            self.warm_up(background=True)
        self._ready.wait(timeout)
        return self.available

    def status(self) -> Dict[str, bool]:
        """Instant, non-blocking readiness snapshot for the warmup endpoint.
        Lets the questionnaire's periodic ping confirm the refiner is hot
        (or still loading) alongside the psychology layer, without waiting."""
        return {
            "started": self._load_started,
            "ready": self._ready.is_set(),
            "available": self.available,
        }

    # ------------------------------------------------------------ profiles

    def _get_cluster_profiles(
        self, test_id: str, trait_names: List[str]
    ) -> Optional[Dict[str, Dict[str, float]]]:
        if test_id in self._cluster_profiles_cache:
            return self._cluster_profiles_cache[test_id]

        trait_path = os.path.join(MODELS_DIR, f"{test_id}_trait_matrix.npy")
        kmeans_path = os.path.join(MODELS_DIR, f"{test_id}_kmeans.pkl")
        umap10d_path = os.path.join(MODELS_DIR, f"{test_id}_umap10d_matrix.npy")

        if not os.path.exists(trait_path) or not os.path.exists(kmeans_path):
            return None

        traits = np.load(trait_path)
        with open(kmeans_path, "rb") as f:
            kmeans = pickle.load(f)

        if os.path.exists(umap10d_path):
            X = np.load(umap10d_path)
            n = min(len(X), len(traits))
            X, traits = X[:n], traits[:n]
        else:
            X = traits

        n_features = kmeans.cluster_centers_.shape[1]
        if X.shape[1] != n_features:
            if X.shape[1] > n_features:
                X = X[:, :n_features]
            else:
                X = np.pad(X, ((0, 0), (0, n_features - X.shape[1])))

        labels = kmeans.predict(X)

        profiles: Dict[str, Dict[str, float]] = {}
        n_traits = min(len(trait_names), traits.shape[1])
        for cid in range(kmeans.n_clusters):
            mask = labels == cid
            if mask.sum() == 0:
                continue
            means = traits[mask].mean(axis=0)
            profiles[str(cid)] = {
                trait_names[i]: round(float(means[i]), 3) for i in range(n_traits)
            }

        self._cluster_profiles_cache[test_id] = profiles
        return profiles

    # ------------------------------------------------------------- helpers

    @staticmethod
    def _format_context(context_notes: Optional[List[Dict]]) -> str:
        if not context_notes:
            return ""
        lines = []
        for entry in context_notes:
            note = (entry.get("note") or "").strip()
            if not note:
                continue
            question = (entry.get("question") or "").strip()
            if question:
                lines.append(f'  On "{question}" they noted: {note}')
            else:
                lines.append(f"  They noted: {note}")
        if not lines:
            return ""
        return (
            "Additional context the person volunteered about specific items:\n"
            + "\n".join(lines)
            + "\n\n"
        )

    @staticmethod
    def _format_responses(raw_responses: Optional[Dict[str, int]]) -> str:
        """Compact rendering of every answer the person chose, so the model
        sees the full response record without a token explosion."""
        if not raw_responses:
            return ""
        pairs = " ".join(f"{qid}={val}" for qid, val in raw_responses.items())
        return f"Their raw item responses (question id = chosen option):\n  {pairs}\n\n"

    def _generate(self, prompt: str, max_new_tokens: int, sample: bool = False) -> str:
        import torch

        messages = [{"role": "user", "content": prompt}]
        text = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(text, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.to(self._model.device) for k, v in inputs.items()}

        gen_kwargs = dict(max_new_tokens=max_new_tokens)
        if sample:
            gen_kwargs.update(do_sample=True, temperature=0.7, top_p=0.9)
        else:
            gen_kwargs.update(do_sample=False)

        with torch.no_grad():
            outputs = self._model.generate(**inputs, **gen_kwargs)

        return self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        ).strip()

    # --------------------------------------------------------------- refine

    def refine(
        self,
        test_id: str,
        trait_scores: Dict[str, float],
        proposed_cluster: str,
        percentiles: Dict[str, int],
        context_notes: Optional[List[Dict]] = None,
        raw_responses: Optional[Dict[str, int]] = None,
    ) -> Optional[str]:
        if not self.wait_until_ready():
            return None

        trait_names = list(trait_scores.keys())
        profiles = self._get_cluster_profiles(test_id, trait_names)
        if not profiles or len(profiles) < 2:
            return None

        trait_lines = "\n".join(
            f"  {name}: {score:.2f} ({percentiles.get(name, 50)}th percentile)"
            for name, score in trait_scores.items()
        )

        group_lines = ""
        for cid, profile in sorted(profiles.items()):
            entries = ", ".join(f"{k}: {v:.2f}" for k, v in profile.items())
            group_lines += f"  Group {cid}: {entries}\n"

        context_block = self._format_context(context_notes)
        responses_block = self._format_responses(raw_responses)

        k = len(profiles)
        prompt = (
            f"A person completed the {test_id.replace('_', ' ')} psychological assessment.\n\n"
            f"Their scored trait profile:\n{trait_lines}\n\n"
            f"{responses_block}"
            f"Population groups identified by clustering:\n{group_lines}\n"
            f"{context_block}"
            f"Current assignment: Group {proposed_cluster}.\n"
            f"The scored trait profile is the primary evidence. "
            f"If the person provided extra context, weigh it only where it genuinely "
            f"clarifies or qualifies their scores, and keep the current assignment "
            f"unless the combined evidence clearly points to a better-fitting group.\n\n"
            f"Reply with ONE line of strict JSON, nothing else, in this form:\n"
            f'{{"group": <0-{k - 1}>, "name": "The <2-4 word archetype name>", '
            f'"tagline": "<one short sentence>", "adjustments": {{"<trait>": <-5 to 5>}}}}\n'
            f"Rules: name must be dignified and specific to THIS profile. "
            f"adjustments may nudge at most 2 trait percentiles, only when the "
            f"volunteered context clearly justifies it; otherwise use {{}}."
        )

        try:
            t0 = time.time()
            # Output is one short JSON line; 64 tokens covers it with margin
            # and shaves CPU generation time off the synchronous submit path.
            response = self._generate(prompt, max_new_tokens=64, sample=False)
            print(f"[refiner] refine({test_id}) took {time.time() - t0:.1f}s")
            return self._parse_refine(response, profiles, trait_scores)
        except Exception as e:
            print(f"[refiner] {e}")
            return None

    @staticmethod
    def _parse_refine(response: str, profiles: Dict, trait_scores: Dict) -> Optional[Dict]:
        """Defensive parse of the structured refine reply. Any failure
        degrades gracefully to whatever fields did parse."""
        import json as _json
        import re as _re

        out = {"group": None, "name": None, "tagline": None, "adjustments": {}}

        m = _re.search(r"\{.*\}", response, _re.DOTALL)
        if m:
            try:
                data = _json.loads(m.group(0))
                g = str(data.get("group", "")).strip()
                if g.isdigit() and g in profiles:
                    out["group"] = g
                name = (data.get("name") or "").strip()
                if 3 <= len(name) <= 60:
                    if not name.lower().startswith("the "):
                        name = "The " + name
                    out["name"] = name
                tagline = (data.get("tagline") or "").strip()
                if 3 <= len(tagline) <= 160:
                    out["tagline"] = tagline
                adj = data.get("adjustments") or {}
                if isinstance(adj, dict):
                    cleaned = {}
                    for k_, v_ in list(adj.items())[:2]:
                        if k_ in trait_scores:
                            try:
                                cleaned[k_] = max(-5, min(5, int(round(float(v_)))))
                            except (TypeError, ValueError):
                                continue
                    out["adjustments"] = cleaned
            except Exception:
                pass

        # Last resort: pull a bare group number out of free text.
        if out["group"] is None:
            for ch in response:
                if ch.isdigit() and ch in profiles:
                    out["group"] = ch
                    break

        if out["group"] is None and not out["name"]:
            return None
        return out

    # -------------------------------------------------------------- enrich

    def enrich_insights(
        self,
        test_id: str,
        trait_scores: Dict[str, float],
        percentiles: Dict[str, int],
        base_insights: List[str],
        context_notes: Optional[List[Dict]] = None,
    ) -> List[str]:
        if not context_notes:
            return base_insights
        if not self.wait_until_ready():
            return base_insights

        context_block = self._format_context(context_notes)
        if not context_block:
            return base_insights

        trait_lines = "\n".join(
            f"  {name}: {score:.2f} ({percentiles.get(name, 50)}th percentile)"
            for name, score in trait_scores.items()
        )

        existing = "\n".join(f"  - {i}" for i in base_insights)

        prompt = (
            f"A person completed the {test_id.replace('_', ' ')} personality assessment.\n\n"
            f"Trait scores:\n{trait_lines}\n\n"
            f"Existing observations:\n{existing}\n\n"
            f"{context_block}"
            f"Write 1-2 brief, personalized observations that connect their "
            f"self-reported context to their trait profile. Each observation "
            f"must be one clear sentence. Do not repeat or rephrase the "
            f"existing observations. Focus on what the personal context "
            f"reveals that the scores alone do not."
        )

        try:
            t0 = time.time()
            # 1-2 sentences of context enrichment fit in ~120 tokens; the old
            # 180 mostly generated tokens that got trimmed anyway. Fewer tokens
            # = a shorter wait on the synchronous submit path.
            response = self._generate(prompt, max_new_tokens=120, sample=True)
            print(f"[refiner] enrich({test_id}) took {time.time() - t0:.1f}s")

            enriched = list(base_insights)
            for line in response.split("\n"):
                line = line.strip().lstrip("-•· 0123456789.)")
                line = line.strip()
                if line and 20 < len(line) < 300:
                    enriched.append(line)

            return enriched[:5]
        except Exception as e:
            print(f"[refiner] enrich: {e}")
            return base_insights
