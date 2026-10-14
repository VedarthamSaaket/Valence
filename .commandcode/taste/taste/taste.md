# Taste
- Prefers to handle authentication/login himself (e.g., logging into GitHub in the browser) rather than having the agent inject or use stored credentials/tokens on his behalf. Confidence: 0.5
- Comfortable with the agent launching GUI/web flows on his machine to unblock manual steps (e.g., opening a login page with `open`). Confidence: 0.5
- Strongly prefers the lowest-friction route and pushes back on anything requiring him to do manual credential/token setup or step-by-step configuration ("ion wanna do anything of that sort ... any other way?"); wants the agent to find or execute an alternative rather than hand him instructions. Confidence: 0.7
- Leans toward zero-install solutions — chose a browser-based web-UI upload over installing new CLI tooling (e.g., `brew install gh`), and followed through on that path without installing anything. Confidence: 0.6
- Low concern for repo hygiene/cleanup of non-code files — explicitly says as long as the actual code files are all present he doesn't care about leftover stale/unnecessary non-code files ("as long sa codefiles are all there idc"). Confidence: 0.5
- Willing to do manual grunt work when the agent hands him an explicit, enumerated list of exact steps/items (e.g., asked the agent to "tell me which ones to remove" rather than acting blind). Confidence: 0.45
- Not fluent with Git internals (asked whether a GitHub web "Commit changes" also pushes); benefits from terse, plain confirmation of whether an action completed and what side effects it had. Confidence: 0.4
