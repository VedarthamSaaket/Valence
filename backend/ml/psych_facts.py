from typing import Dict, List

from ml.psych_bibliography import BIBLIOGRAPHY, _label

H, L, M = "high", "low", "mid"
MAX_FACTS = 4
MAX_MYTHS = 3
MAX_LINKS = 4
STRONG, PARTIAL = "strong", "partial"
PARTIAL_TESTS = {"fti"}

EXTRA_SOURCES: Dict[str, str] = {
    "Hilbig & Zettler (2009)": "Hilbig, B. E., & Zettler, I. (2009). Pillars of cooperation: Honesty-Humility, social value orientations, and economic behavior. Journal of Research in Personality, 43(3), 516-519.",
    "Lee & Ashton (2005)": "Lee, K., & Ashton, M. C. (2005). Psychopathy, Machiavellianism, and narcissism in the Five-Factor Model and the HEXACO model of personality structure. Personality and Individual Differences, 38(7), 1571-1582.",
    "Roberts et al. (2006)": "Roberts, B. W., Walton, K. E., & Viechtbauer, W. (2006). Patterns of mean-level change in personality traits across the life course: A meta-analysis of longitudinal studies. Psychological Bulletin, 132(1), 1-25.",
    "Roberts et al. (2007)": "Roberts, B. W., Kuncel, N. R., Shiner, R., Caspi, A., & Goldberg, L. R. (2007). The power of personality: The comparative validity of personality traits, socioeconomic status, and cognitive ability for predicting important life outcomes. Perspectives on Psychological Science, 2(4), 313-345.",
    "Costa & McCrae (1980)": "Costa, P. T., & McCrae, R. R. (1980). Influence of extraversion and neuroticism on subjective well-being: Happy and unhappy people. Journal of Personality and Social Psychology, 38(4), 668-678.",
    "Kaufman et al. (2016)": "Kaufman, S. B., Quilty, L. C., Grazioplene, R. G., Hirsh, J. B., Gray, J. R., Peterson, J. B., & DeYoung, C. G. (2016). Openness to experience and intellect differentially predict creative achievement in the arts and sciences. Journal of Personality, 84(2), 248-258.",
    "Judge et al. (2012)": "Judge, T. A., Livingston, B. A., & Hurst, C. (2012). Do nice guys, and gals, really finish last? The joint effects of sex and agreeableness on income. Journal of Personality and Social Psychology, 102(2), 390-407.",
    "Paulhus (1998)": "Paulhus, D. L. (1998). Interpersonal and intrapsychic adaptiveness of trait self-enhancement: A mixed blessing? Journal of Personality and Social Psychology, 74(5), 1197-1208.",
    "Christie & Geis (1970)": "Christie, R., & Geis, F. L. (1970). Studies in Machiavellianism. Academic Press.",
    "Back et al. (2010)": "Back, M. D., Schmukle, S. C., & Egloff, B. (2010). Why are narcissists so charming at first sight? Decoding the narcissism-popularity link at zero acquaintance. Journal of Personality and Social Psychology, 98(1), 132-145.",
    "Wetzel et al. (2017)": "Wetzel, E., Brown, A., Hill, P. L., Chung, J. M., Robins, R. W., & Roberts, B. W. (2017). The narcissism epidemic is dead; long live the narcissism epidemic. Psychological Science, 28(12), 1833-1847.",
    "Foster et al. (2003)": "Foster, J. D., Campbell, W. K., & Twenge, J. M. (2003). Individual differences in narcissism: Inflated self-views across the lifespan and around the world. Journal of Research in Personality, 37(6), 469-486.",
    "Killingsworth & Gilbert (2010)": "Killingsworth, M. A., & Gilbert, D. T. (2010). A wandering mind is an unhappy mind. Science, 330(6006), 932.",
    "Lieberman et al. (2007)": "Lieberman, M. D., Eisenberger, N. I., Crockett, M. J., Tom, S. M., Pfeifer, J. H., & Way, B. M. (2007). Putting feelings into words: Affect labeling disrupts amygdala activity in response to affective stimuli. Psychological Science, 18(5), 421-428.",
    "Vernon et al. (2008)": "Vernon, P. A., Martin, R. A., Schermer, J. A., & Mackie, A. (2008). A behavioral genetic investigation of humor styles and their correlations with the Big-5 personality dimensions. Personality and Individual Differences, 44(5), 1116-1125.",
    "Oliver & Wood (2014)": "Oliver, J. E., & Wood, T. J. (2014). Conspiracy theories and the paranoid style(s) of mass opinion. American Journal of Political Science, 58(4), 952-966.",
    "Wood et al. (2012)": "Wood, M. J., Douglas, K. M., & Sutton, R. M. (2012). Dead and alive: Beliefs in contradictory conspiracy theories. Social Psychological and Personality Science, 3(6), 767-773.",
    "Swami et al. (2014)": "Swami, V., Voracek, M., Stieger, S., Tran, U. S., & Furnham, A. (2014). Analytic thinking reduces belief in conspiracy theories. Cognition, 133(3), 572-585.",
    "Low et al. (2005)": "Low, K. S. D., Yoon, M., Roberts, B. W., & Rounds, J. (2005). The stability of vocational interests from early adolescence to middle adulthood: A quantitative review of longitudinal studies. Psychological Bulletin, 131(5), 713-737.",
    "Nye et al. (2012)": "Nye, C. D., Su, R., Rounds, J., & Drasgow, F. (2012). Vocational interests and performance: A quantitative summary of over 60 years of research. Perspectives on Psychological Science, 7(4), 384-403.",
    "Su et al. (2009)": "Su, R., Rounds, J., & Armstrong, P. I. (2009). Men and things, women and people: A meta-analysis of sex differences in interests. Psychological Bulletin, 135(6), 859-884.",
    "Larson et al. (2002)": "Larson, L. M., Rottinghaus, P. J., & Borgen, F. H. (2002). Meta-analyses of Big Six interests and Big Five personality factors. Journal of Vocational Behavior, 61(2), 217-239.",
    "Fraley (2002)": "Fraley, R. C. (2002). Attachment stability from infancy to adulthood: Meta-analysis and dynamic modeling of developmental mechanisms. Personality and Social Psychology Review, 6(2), 123-151.",
    "Fraley et al. (2015)": "Fraley, R. C., Hudson, N. W., Heffernan, M. E., & Segal, N. (2015). Are adult attachment styles categorical or dimensional? A taxometric analysis of general and relationship-specific attachment orientations. Journal of Personality and Social Psychology, 109(2), 354-368.",
    "Fraley & Shaver (1998)": "Fraley, R. C., & Shaver, P. R. (1998). Airport separations: A naturalistic study of adult attachment dynamics in separating couples. Journal of Personality and Social Psychology, 75(5), 1198-1212.",
    "McCrae & Costa (1989)": "McCrae, R. R., & Costa, P. T. (1989). Reinterpreting the Myers-Briggs Type Indicator from the perspective of the five-factor model of personality. Journal of Personality, 57(1), 17-40.",
    "Noftle & Shaver (2006)": "Noftle, E. E., & Shaver, P. R. (2006). Attachment dimensions and the Big Five personality traits: Associations and comparative ability to predict relationship quality. Journal of Research in Personality, 40(2), 179-208.",
    "Goreis & Voracek (2019)": "Goreis, A., & Voracek, M. (2019). A systematic review and meta-analysis of psychological research on conspiracy beliefs: Field characteristics, measurement instruments, and associations with personality traits. Frontiers in Psychology, 10, 205.",
    "Chopik et al. (2013)": "Chopik, W. J., Edelstein, R. S., & Fraley, R. C. (2013). From the cradle to the grave: Age differences in attachment from early adulthood to old age. Journal of Personality, 81(2), 171-183.",
}

FACTS: Dict[str, List[tuple]] = {
    "hexaco": [
        ({"Honesty-Humility": H}, "In experiments where one person decides how to split money with a stranger who has no say, people high in Honesty-Humility hand over a fairer share, even though nothing stops them keeping it all.", "Hilbig & Zettler (2009)"),
        ({"Honesty-Humility": L}, "Honesty-Humility is the HEXACO factor that tracks the Dark Triad most closely: narcissism, Machiavellianism and psychopathy all go with lower scores on it.", "Lee & Ashton (2005)"),
        ({"Honesty-Humility": H, "Agreeableness": L}, "Your two cooperation factors point in different directions, which the model allows for: Honesty-Humility is about not exploiting people, Agreeableness is about not retaliating. A person can be scrupulously fair and still quick to push back.", "Ashton et al. (2014)"),
        ({"Honesty-Humility": L, "Agreeableness": H}, "Your two cooperation factors point in different directions, which the model allows for: Agreeableness is about patience and forgiveness, Honesty-Humility is about not seeking an edge over others. A person can be easy-going and still keen to come out ahead.", "Ashton et al. (2014)"),
        ({"Conscientiousness": H}, "Across a meta-analysis covering many areas of psychology, Conscientiousness was the HEXACO factor most consistently tied to achievement and self-control outcomes.", "Zettler et al. (2020)"),
        ({"Openness": H}, "Across a large meta-analysis, Openness to Experience was the HEXACO factor linked to creativity, curiosity and unconventional interests.", "Zettler et al. (2020)"),
        ({"Emotionality": L}, "Low Emotionality is about needing less emotional support and worrying less under threat. In the HEXACO model it is treated as a different way of handling risk, with its own costs and benefits, and is not a lack of feeling.", "Ashton & Lee (2007)"),
        ({}, "On these six factors, people who know you well tend to describe you much as you describe yourself. Self-reports and reports from acquaintances agree substantially.", "Lee & Ashton (2018)"),
        ({}, "The sixth factor, Honesty-Humility, was found by studying personality words in many languages. The same six groupings kept reappearing, which is why this model has six factors where older ones have five.", "Ashton & Lee (2007)"),
    ],
    "ambi": [
        ({"Conscientiousness": H}, "A review of long-term studies found that personality traits predict how long people live, whether they divorce and how far they get at work about as well as income background or intelligence do. Conscientiousness was a consistent predictor of longer life.", "Roberts et al. (2007)"),
        ({"Extraversion": H}, "Extraversion is the trait most tied to how much positive feeling people report day to day. It says little about how much negative feeling they have, which runs on a separate track.", "Costa & McCrae (1980)"),
        ({"Extraversion": L}, "Lower Extraversion goes with reporting less day-to-day excitement, but it does not go with more distress. Positive and negative feelings run on separate tracks, and negative feeling is tied to Neuroticism.", "Costa & McCrae (1980)"),
        ({"Neuroticism": H}, "Neuroticism is the trait most tied to how much negative feeling people report, and it is largely independent of how much positive feeling they have. A person can score high here and still enjoy a great deal.", "Costa & McCrae (1980)"),
        ({"Neuroticism": L}, "Low Neuroticism goes with reporting fewer negative feelings over time. It is one of three traits, with Agreeableness and Conscientiousness, that form a broader Stability factor.", "DeYoung (2006)"),
        ({"Openness": H}, "Openness predicts creative achievement in the arts in particular. The closely related trait of Intellect is what predicts creative achievement in the sciences.", "Kaufman et al. (2016)"),
        ({"Agreeableness": L}, "Lower agreeableness goes with somewhat higher earnings on average, an effect that was stronger for men than for women in the samples studied.", "Judge et al. (2012)"),
        ({"Agreeableness": H}, "Agreeableness, with Conscientiousness and emotional stability, forms a broader Stability factor that reflects keeping emotions, relationships and goals on an even keel.", "DeYoung (2006)"),
        ({"Conscientiousness": L}, "Conscientiousness is the trait that rises most reliably as people move through adulthood, so a lower score now often climbs with age and responsibility.", "Roberts et al. (2006)"),
        ({}, "The five domains measured here show up whether people rate themselves or are rated by others who know them, and across very different questionnaires.", "McCrae & Costa (1987)"),
    ],
    "darktriad": [
        ({"Narcissism": H}, "People who rate themselves very favourably make a strong first impression: in a study of weekly group meetings they were seen as agreeable and competent at the first meeting. By the seventh, the same group rated them negatively.", "Paulhus (1998)"),
        ({"Psychopathy": H}, "In a meta-analysis of the Dark Triad literature, psychopathy was the trait of the three most strongly tied to difficult outcomes with other people. It is a statistical tendency across many studies, not a prediction about any one person.", "Muris et al. (2017)"),
        ({"Machiavellianism": H}, "What separates Machiavellianism from psychopathy on this test is impulse control: the Machiavellian style is patient and planned, where psychopathy is impulsive.", "Jones & Paulhus (2014)"),
        ({"Machiavellianism": M, "Narcissism": M}, "Mid-range scores are the norm on this test. The Dark Triad was defined by studying ordinary students, and its traits are spread across the general population in degrees.", "Paulhus & Williams (2002)"),
        ({"Machiavellianism": L, "Narcissism": L, "Psychopathy": L}, "The one Big-Five trait all three dark traits share is low agreeableness, so a profile that is low on all three usually goes with being cooperative and considerate.", "Paulhus & Williams (2002)"),
        ({}, "The Machiavellianism scale began with two psychologists turning statements from Machiavelli's writings into questionnaire items to see who agreed with them.", "Christie & Geis (1970)"),
        ({}, "When the items of this test are analysed one by one, the Machiavellianism and psychopathy items are hard to tell apart, while the narcissism items stand on their own.", "Persson et al. (2019)"),
    ],
    "npi": [
        ({"Exhibitionism": H}, "People who score high on narcissism were liked more at first sight in a study of strangers introducing themselves, and the reasons were visible ones: neater and flashier dress, a charming expression, confident movement and humour.", "Back et al. (2010)"),
        ({"Authority": H}, "The leadership side of this test, which is where you score high, is the part linked to good outcomes such as self-esteem and social confidence.", "Ackerman et al. (2011)"),
        ({"Entitlement": H}, "Entitlement is the part of narcissism with the clearest social cost: in experiments it predicted taking more than a fair share and making competitive choices over shared resources.", "Campbell et al. (2004)"),
        ({"Authority": H, "Exploitativeness": L}, "A profile with high leadership and low exploitativeness resembles the subgroup that studies found to be the best adjusted of the narcissism profiles: admiration-seeking without the rivalry.", "Wetzel et al. (2016)"),
        ({"Superiority": L, "Exhibitionism": L}, "Low scores on the admiration-seeking scales mean little appetite for standing out or being admired, which goes with a more modest social style.", "Back et al. (2013)"),
        ({}, "Scores on this test tend to fall with age: across a large international sample, older adults scored lower than younger adults.", "Foster et al. (2003)"),
        ({}, "Narcissism has two sides with opposite social effects: admiration (charm, assertiveness) tends to win people over, rivalry (putting others down) tends to push them away.", "Back et al. (2013)"),
    ],
    "dass": [
        ({"Stress": H, "Anxiety": L}, "Stress on this test is its own dimension: tension, irritability and difficulty winding down. It can be raised without the fear and physical arousal that define the anxiety scale, which is the pattern in your scores.", "Lovibond & Lovibond (1995)"),
        ({"Depression": H, "Anxiety": H}, "Depression and anxiety scores rise together for many people because they share a common core of general distress. What separates them is low positive feeling on the depression side and physical arousal on the anxiety side.", "Clark & Watson (1991)"),
        ({"Anxiety": H, "Depression": L}, "Physical arousal, such as a racing heart or trembling, is what is specific to anxiety on this test. It can be raised while the capacity for enjoyment, which the depression scale tracks, stays intact.", "Clark & Watson (1991)"),
        ({"Depression": L, "Anxiety": L, "Stress": L}, "Low scores are the most common result: in general-population samples most adults score toward the bottom of all three scales.", "Henry & Crawford (2005)"),
        ({}, "This test asks about the past week only, so it captures a recent state. The same person can score very differently a month apart.", "Lovibond & Lovibond (1995)"),
        ({}, "The stress scale was not planned. It emerged from the data while the authors were trying to separate depression from anxiety, as a third cluster of tension and irritability.", "Lovibond & Lovibond (1995)"),
    ],
    "kims": [
        ({"Acting with Awareness": L}, "Minds wander a lot: in a study that pinged thousands of people at random moments, they were thinking about something other than what they were doing in about 47% of samples, and reported being less happy at those moments.", "Killingsworth & Gilbert (2010)"),
        ({"Acting with Awareness": H}, "Present-centred attention, the skill you score high on, was linked to greater well-being and more self-directed behaviour in diary and experience-sampling studies.", "Brown & Ryan (2003)"),
        ({"Describing": H}, "Putting a feeling into words has a measurable effect: in a brain-imaging study, naming the emotion in a face reduced the amygdala's response to it.", "Lieberman et al. (2007)"),
        ({"Describing": L}, "Putting a feeling into words has a measurable effect: in a brain-imaging study, naming the emotion in a face reduced the amygdala's response to it. Describing is a skill on this test because it can be practised.", "Lieberman et al. (2007)"),
        ({"Observing": H, "Accepting without Judgment": L}, "Noticing a lot while judging what you notice is a recognised pattern. In a study of mindfulness profiles, this 'judgmentally observing' group reported the most emotional difficulty of the four groups found.", "Pearson et al. (2015)"),
        ({"Acting with Awareness": H, "Accepting without Judgment": H}, "High awareness with high acceptance matches the 'non-judgmentally aware' profile, which reported good emotional outcomes in a study of mindfulness subgroups.", "Pearson et al. (2015)"),
        ({}, "The four skills on this test were drawn from dialectical behaviour therapy, where they are taught as separate, learnable skills.", "Baer et al. (2004)"),
    ],
    "hsq": [
        ({"Self-Enhancing": H}, "Of the four humor styles, self-enhancing humor, keeping an amused outlook when things go wrong, has the strongest positive link with mental health across studies.", "Schneider et al. (2018)"),
        ({"Aggressive": H}, "Aggressive humor is hard on the people it targets, but across studies it shows almost no link, good or bad, with the mental health of the person using it.", "Schneider et al. (2018)"),
        ({"Self-Defeating": H}, "Self-defeating humor, getting laughs at your own expense to be accepted, is the one style consistently linked with lower well-being across studies.", "Schneider et al. (2018)"),
        ({"Affiliative": H, "Self-Enhancing": H, "Aggressive": L, "Self-Defeating": L}, "High on the two benign styles and low on the two harmful ones is one of four recurring humor patterns found by cluster analysis, and it went with higher self-esteem.", "Galloway (2010)"),
        ({"Affiliative": L, "Self-Enhancing": L}, "Using little humor of any kind is a recognised pattern of its own, described in one study as 'humor deniers'.", "Leist & Mueller (2013)"),
        ({}, "Humor styles run in families partly through genes: a twin study found that individual differences in all four styles were in part heritable.", "Vernon et al. (2008)"),
        ({}, "In the study that introduced this test, men scored higher than women on aggressive and self-defeating humor, while the two benign styles showed little or no difference.", "Martin et al. (2003)"),
    ],
    "gcbs": [
        ({"Government Malfeasance": H}, "People who believe one conspiracy theory tend to believe others, even ones that contradict it. In one study, the more people thought Princess Diana faked her death, the more they also thought she was murdered.", "Wood et al. (2012)"),
        ({"Malevolent Global": H}, "People who believe one conspiracy theory tend to believe others, even ones that contradict it. In one study, the more people thought Princess Diana faked her death, the more they also thought she was murdered.", "Wood et al. (2012)"),
        ({"Control of Information": H}, "Thinking style matters: in experiments, prompting people to think analytically reduced how much they endorsed conspiracy theories.", "Swami et al. (2014)"),
        ({"Government Malfeasance": L, "Malevolent Global": L}, "Low scores across themes reflect a low general tendency toward conspiracy explanations. People differ mainly in that overall tendency, and far less in which particular theme they favour.", "Frenken & Imhoff (2021)"),
        ({}, "Across five data sets, people differed mostly in how much they believed overall, and the most strongly believing groups were the smallest.", "Frenken & Imhoff (2021)"),
        ({}, "This test never names a real event. It asks about general themes so that it measures a way of thinking, without depending on whichever theories are in the news.", "Brotherton et al. (2013)"),
        ({}, "Conspiracy mentality behaves like a stable political attitude and goes with distrust of groups seen as powerful, whoever they happen to be.", "Imhoff & Bruder (2014)"),
    ],
    "riasec": [
        ({"Realistic": H}, "Realistic interests sit at the 'Things' end of the Things-versus-People dimension, the single dimension on which men's and women's average interests differ most.", "Su et al. (2009)"),
        ({"Artistic": H, "Conventional": L}, "Artistic and Conventional sit on opposite sides of Holland's hexagon, so high on one and low on the other is exactly the pattern the model expects.", "Tracey & Rounds (1993)"),
        ({"Social": H, "Realistic": L}, "Social and Realistic sit on opposite sides of Holland's hexagon, which matches a preference for working with people over working with things.", "Prediger (1982)"),
        ({}, "Interests are among the most stable things about a person: they hold steadier over time than personality traits do, and settle further through the college years.", "Low et al. (2005)"),
        ({}, "Interests predict more than what you will enjoy. Across sixty years of studies they also predicted how well people performed and whether they stayed, most of all when the interest matched the job or course.", "Nye et al. (2012)"),
    ],
    "attachment": [
        ({"Avoidant": H}, "Researchers once watched couples saying goodbye at an airport. Among those who were separating, the more avoidant partners sought less contact and pulled away more, a pattern that was clearest in women.", "Fraley & Shaver (1998)"),
        ({"Anxious": H}, "Attachment anxiety is highest in young adulthood and lower in middle and older age, in a study of more than 86,000 adults.", "Chopik et al. (2013)"),
        ({"Anxious": H, "Avoidant": L}, "High anxiety with low avoidance is the pattern called 'preoccupied': a positive view of others alongside doubt about one's own worth to them.", "Bartholomew & Horowitz (1991)"),
        ({"Anxious": L, "Avoidant": H}, "Low anxiety with high avoidance is the pattern called 'dismissing': a positive view of oneself alongside wariness about depending on others.", "Bartholomew & Horowitz (1991)"),
        ({"Anxious": H, "Avoidant": H}, "High anxiety with high avoidance is the pattern called 'fearful': wanting closeness while expecting to be hurt by it.", "Bartholomew & Horowitz (1991)"),
        ({"Anxious": L, "Avoidant": L}, "Low anxiety with low avoidance is the pattern called 'secure': comfort with closeness and with being on one's own.", "Bartholomew & Horowitz (1991)"),
        ({}, "The same person can be secure with a friend and anxious with a partner. When attachment is measured separately for each relationship, people vary meaningfully from one to the next.", "Fraley et al. (2011)"),
    ],
    "fti": [
        ({"Director": H, "Negotiator": L}, "One study linked these two scales to finger length: a relatively longer ring finger, an indirect sign of hormone exposure before birth, went with higher Director scores, and the opposite pattern with higher Negotiator scores.", "Fisher et al. (2010)"),
        ({"Negotiator": H, "Director": L}, "One study linked these two scales to finger length: a relatively longer ring finger, an indirect sign of hormone exposure before birth, went with higher Director scores, and the opposite pattern with higher Negotiator scores.", "Fisher et al. (2010)"),
        ({"Explorer": H, "Builder": L}, "High novelty seeking with low caution is a combination an older temperament model also describes, as an exploratory, uninhibited style.", "Cloninger (1987)"),
        ({"Builder": H, "Explorer": L}, "High caution with low novelty seeking is a combination an older temperament model also describes, as a careful, orderly style.", "Cloninger (1987)"),
        ({}, "In two brain-imaging studies, scores on each of the four scales went with activity in brain regions consistent with the chemical system that scale is proposed to reflect.", "Brown et al. (2013)"),
    ],
}

MYTHS: Dict[str, List[tuple]] = {
    "hexaco": [
        ({"Emotionality": H}, "A high Emotionality score means being emotionally unstable.", "In the HEXACO model, Emotionality covers fearfulness, anxiety, sentimentality and wanting support from close others. Irritability and anger are not part of it; they belong to low Agreeableness. High Emotionality is closer to sensitivity and attachment than to instability.", "Ashton & Lee (2007)"),
        ({"Honesty-Humility": L}, "A low Honesty-Humility score means being a dishonest person.", "The factor measures tendencies across many people: an interest in status and advantage, and less discomfort with bending rules. It is linked to exploitative behaviour on average across studies, which is a statistical trend and not a verdict on an individual.", "Zettler et al. (2020)"),
        ({}, "Personality has five dimensions.", "Studies of personality words across many languages repeatedly recover six. The sixth, Honesty-Humility, captures fairness and modesty that five-factor models fold into Agreeableness.", "Ashton & Lee (2007)"),
        ({}, "A personality profile puts you in a box.", "Five profiles do recur across samples of about 90,000 people each, but they describe common patterns across the six factors. Your six scores carry more information than any profile label.", "Espinoza et al. (2020)"),
    ],
    "ambi": [
        ({}, "Personality is fixed once you are an adult.", "A meta-analysis of 92 long-term studies found that traits keep shifting across adult life. On average people become more conscientious and more emotionally stable, with the most change in young adulthood.", "Roberts et al. (2006)"),
        ({}, "Everyone belongs to a distinct personality type.", "An analysis of more than 1.5 million respondents did find four types, but as regions where people cluster slightly more densely. Most people sit near the average, and the types have no sharp borders.", "Gerlach et al. (2018)"),
        ({"Neuroticism": H}, "A high Neuroticism score means being unhappy.", "Negative and positive feelings are largely independent. Neuroticism predicts more negative feeling, while positive feeling is tied to Extraversion, so a person can have plenty of both.", "Costa & McCrae (1980)"),
        ({"Extraversion": L}, "Lower Extraversion means being less happy with life.", "Extraversion relates to how much positive excitement people report, and it is unrelated to how much distress they feel. Low Extraversion is a quieter style, not an unhappier one.", "Costa & McCrae (1980)"),
        ({}, "Personality tests only tell you what you already think of yourself.", "The same five domains appear when other people rate you, and their ratings agree substantially with self-ratings. The traits describe something others can see.", "McCrae & Costa (1987)"),
    ],
    "darktriad": [
        ({"Psychopathy": H}, "A high psychopathy score means someone is a psychopath.", "This test measures subclinical psychopathy: impulsivity, thrill-seeking and lower concern for others, as they vary across ordinary people. The Dark Triad was defined in non-clinical samples, and a score here is a position on a continuum, not a diagnosis.", "Paulhus & Williams (2002)"),
        ({"Narcissism": H}, "A high narcissism score means narcissistic personality disorder.", "The narcissism measured here is the subclinical kind, studied in ordinary samples: grandiosity and a wish for admiration that vary by degree in everyone. It is not a clinical assessment.", "Paulhus & Williams (2002)"),
        ({}, "The three dark traits are really one trait with three names.", "They overlap, but the original study found them distinct, each with its own pattern of correlates. Later item-level work adds a nuance: on this test Machiavellianism and psychopathy are hard to separate, while narcissism stands apart.", "Persson et al. (2019)"),
        ({}, "Dark traits are rare and belong to a small group of bad people.", "The traits are spread across the general population by degree. A decade of research treated them as normal-range personality dimensions with distinct everyday correlates at work, in study and in relationships.", "Furnham et al. (2013)"),
    ],
    "npi": [
        ({}, "A high score on this test means narcissistic personality disorder.", "The test was built for the general population and measures narcissism as a normal personality trait. Its total mixes healthy content, such as leadership and confidence, with unhealthy content, such as entitlement, so the total alone says little about problems.", "Ackerman et al. (2011)"),
        ({}, "Young people today are more narcissistic than earlier generations.", "A study of American students from the 1990s to the 2010s that checked whether the test measured the same thing in each cohort found no rise. Scores had slightly declined.", "Wetzel et al. (2017)"),
        ({"Authority": H}, "Every part of narcissism is harmful.", "The Leadership/Authority part, where you score high, is associated with adaptive outcomes. It is the Entitlement/Exploitativeness part that carries the social costs.", "Ackerman et al. (2011)"),
        ({"Exhibitionism": H}, "Narcissists are disliked.", "At first meeting the opposite is true: people high in narcissism were more popular with strangers. The costs appear later and are tied to the rivalry side of narcissism, not to the wish for admiration.", "Back et al. (2013)"),
    ],
    "dass": [
        ({}, "A high score means you have depression or an anxiety disorder.", "The scales measure how intense certain experiences were over the past week, on a continuum that runs through the whole population. They were designed to describe severity by degree, and they cannot say whether a disorder is present.", "Crawford & Henry (2003)"),
        ({}, "Stress and anxiety are the same thing.", "On this test they separate. Anxiety is fear and physical arousal; stress is tension, irritability and being unable to relax. Many people are raised on one and not the other.", "Lovibond & Lovibond (1995)"),
        ({"Depression": H, "Anxiety": H}, "Scoring high on depression and anxiety together means two separate problems.", "Both scales tap a shared core of general distress, which is why they so often rise together. The tripartite model treats that shared part as one thing with two distinct additions.", "Clark & Watson (1991)"),
    ],
    "kims": [
        ({}, "Mindfulness is one ability that you either have or lack.", "This test was built on the finding that mindfulness breaks into separate skills: observing, describing, acting with awareness and accepting without judgment. People are commonly strong on one and weak on another.", "Baer et al. (2004)"),
        ({"Observing": H}, "The more you notice, the more mindful and the better off you are.", "In people without meditation experience, noticing more does not reliably go with better well-being. Observing helps when it comes with acceptance, and it can go with more distress when it comes with self-judgment.", "Baer et al. (2006)"),
        ({}, "You have to meditate to be mindful.", "Mindful attention varies naturally between people who have never meditated, and those natural differences relate to well-being. Meditators do score higher on most facets, so practice helps, but it is not the only source.", "Brown & Ryan (2003)"),
        ({"Accepting without Judgment": L}, "Being hard on your own thoughts and feelings keeps you sharp.", "Across mindfulness profiles, the groups that judged their inner experience harshly reported worse emotional outcomes, including the group that was otherwise highly observant.", "Pearson et al. (2015)"),
    ],
    "hsq": [
        ({}, "A good sense of humor is always good for you.", "It depends on the style. Across a meta-analysis, self-enhancing and affiliative humor went with better mental health, self-defeating humor with worse, and aggressive humor made little difference either way.", "Schneider et al. (2018)"),
        ({"Self-Defeating": H}, "Making fun of yourself is harmless modesty.", "Gently not taking yourself too seriously is healthy, and it belongs to the affiliative and self-enhancing styles. The self-defeating style is different: putting yourself down to win approval, which was linked with lower self-esteem and more distress.", "Martin et al. (2003)"),
        ({"Aggressive": H}, "Teasing and sarcasm are a sign of hidden unhappiness.", "Across studies, aggressive humor was largely unrelated to the mental health of the person using it. Its costs fall on relationships, not on mood.", "Schneider et al. (2018)"),
        ({}, "Funny people use every kind of humor.", "Cluster analyses find distinct patterns: some people use all four styles, some use few, some only the benign ones and some mainly the harmful ones.", "Galloway (2010)"),
    ],
    "gcbs": [
        ({}, "Only a small fringe believes in conspiracy theories.", "In national surveys in the United States, about half of the public endorsed at least one conspiracy theory. Belief is a matter of degree across the whole population.", "Oliver & Wood (2014)"),
        ({}, "Believing in conspiracies means something is wrong with a person.", "Reviews trace these beliefs to ordinary motives: wanting to understand events, wanting to feel safe and in control, and wanting to think well of one's group.", "Douglas et al. (2017)"),
        ({"Personal Wellbeing Threats": H}, "Conspiracy beliefs make people feel safer and more in control.", "People are drawn to them for those reasons, but the evidence reviewed so far suggests the beliefs often fail to deliver, and may leave people feeling less in control.", "Douglas et al. (2017)"),
        ({}, "People believe a particular theory because of the evidence for that theory.", "The strongest predictor of believing one theory is believing others, including unrelated and even contradictory ones. That points to a general outlook more than to the details of each case.", "Wood et al. (2012)"),
    ],
    "riasec": [
        ({}, "Your interests keep changing, so an interest test says little about the future.", "Interests are remarkably stable from adolescence into middle adulthood, more stable than personality traits over the same periods.", "Low et al. (2005)"),
        ({}, "What matters for doing well is ability; interests only affect enjoyment.", "Sixty years of studies show interests also predict performance and persistence in work and study, most strongly when a person's interests match the environment.", "Nye et al. (2012)"),
        ({}, "Finding a job that matches your type guarantees you will be satisfied.", "The match between interests and environment does relate to satisfaction and staying, but the relationship is modest. It is one ingredient among many.", "Nauta (2010)"),
        ({}, "You are one type.", "Holland's types are arranged in a hexagon and people resemble several at once. Six recurring profiles have been found, each a blend, which is why results are usually read as a two- or three-letter code.", "Perera & McIlveen (2018)"),
    ],
    "attachment": [
        ({}, "Attachment style is set in infancy and never changes.", "A meta-analysis of studies following people from infancy found only moderate stability. Early patterns leave a trace, but there is real room for change across life.", "Fraley (2002)"),
        ({}, "Everyone has one attachment style, and it is a type.", "Statistical tests of whether attachment forms categories or dimensions favour dimensions. People differ by degree on anxiety and avoidance, and the four familiar 'styles' are regions on that map.", "Fraley et al. (2015)"),
        ({}, "Your attachment style is the same with everyone.", "When attachment is measured separately for mother, father, partner and friend, the same person often shows different patterns in different relationships.", "Fraley et al. (2011)"),
        ({"Avoidant": H}, "Avoidant people do not need closeness.", "Avoidance is described as a deactivating strategy: the need for closeness is still there, and the person keeps it turned down to avoid the distress of being let down.", "Mikulincer et al. (2003)"),
        ({"Anxious": H}, "Attachment anxiety is just being needy.", "It is described as a hyperactivating strategy: turning up signals of distress to keep an attachment figure close when their availability feels uncertain.", "Mikulincer et al. (2003)"),
    ],
    "fti": [
        ({}, "The four temperaments are proven brain chemistry.", "The links to dopamine, serotonin, testosterone and estrogen are proposed. Two brain-imaging studies found activity consistent with them, but most of the evidence comes from the test's own developers, and independent confirmation remains limited.", "Shayesteh et al. (2023)"),
        ({}, "You are one of four types.", "Everyone gets a score on all four scales. The scales are continuous and relate to the Big Five in the expected directions, so a result is a mix with a leading scale, not a single type.", "Fisher et al. (2015)"),
        ({"Director": H}, "Being a Director is about having more testosterone.", "The test measures a thinking style, analytical, direct and decisive, through questions. The hormone link is a hypothesis supported by indirect markers, and the test says nothing about anyone's actual hormone levels.", "Fisher et al. (2010)"),
    ],
}


LINKS: Dict[str, List[tuple]] = {
    "hexaco": [
        ({"Honesty-Humility": L}, "People with lower Honesty-Humility like this may also score higher on measures of narcissism, Machiavellianism and psychopathy such as the Short Dark Triad.", "Lee & Ashton (2005)", STRONG),
        ({"Honesty-Humility": H}, "People with higher Honesty-Humility like this may also score lower on measures of narcissism, Machiavellianism and psychopathy such as the Short Dark Triad.", "Lee & Ashton (2005)", STRONG),
        ({"Emotionality": H}, "People with higher Emotionality like this may show somewhat higher Neuroticism on Big Five inventories, though the two differ: Big Five Neuroticism includes irritability, which the HEXACO places elsewhere.", "Ashton & Lee (2007)", STRONG),
        ({"Emotionality": L}, "People with lower Emotionality like this may show somewhat lower Neuroticism on Big Five inventories, though the two differ: Big Five Neuroticism includes irritability, which the HEXACO places elsewhere.", "Ashton & Lee (2007)", STRONG),
    ],
    "ambi": [
        ({"Neuroticism": H}, "Your Neuroticism score describes something the MBTI has no scale for. None of its four preferences captures emotional stability.", "McCrae & Costa (1989)", STRONG),
        ({"Neuroticism": L}, "Your Neuroticism score describes something the MBTI has no scale for. None of its four preferences captures emotional stability.", "McCrae & Costa (1989)", STRONG),
        ({"Conscientiousness": H, "Agreeableness": H, "Neuroticism": L}, "People with this combination may show patterns that fall on the higher-order Stability factor found when Big Five inventories are analysed together.", "DeYoung (2006)", STRONG),
    ],
    "darktriad": [
        ({"Psychopathy": H}, "People with higher psychopathy scores like this may also show lower Agreeableness and lower Conscientiousness on Big Five inventories.", "Paulhus & Williams (2002)", STRONG),
        ({"Narcissism": H}, "People with higher narcissism scores like this may also show higher Extraversion and Openness, and lower Agreeableness, on Big Five inventories.", "Paulhus & Williams (2002)", STRONG),
        ({"Machiavellianism": H}, "People with higher Machiavellianism scores like this may also show lower Agreeableness and lower Conscientiousness on Big Five inventories.", "Paulhus & Williams (2002)", STRONG),
        ({"Machiavellianism": L, "Narcissism": L, "Psychopathy": L}, "People with low scores on all three traits like this may also show higher Agreeableness on Big Five inventories.", "Paulhus & Williams (2002)", STRONG),
        ({}, "Across people, higher scores on these three traits tend to go with lower Honesty-Humility on the HEXACO inventory, and lower scores with higher Honesty-Humility.", "Lee & Ashton (2005)", STRONG),
    ],
    "npi": [
        ({"Authority": H}, "People with higher leadership scores like this may also show higher Extraversion on Big Five inventories.", "Ackerman et al. (2011)", STRONG),
        ({"Exhibitionism": H}, "People with higher exhibitionism scores like this may also show higher Extraversion on Big Five inventories.", "Ackerman et al. (2011)", STRONG),
        ({"Entitlement": H}, "People with higher entitlement scores like this may also show lower Agreeableness on Big Five inventories and lower Honesty-Humility on the HEXACO.", "Ackerman et al. (2011)", STRONG),
        ({"Exploitativeness": H}, "People with higher exploitativeness scores like this may also show lower Agreeableness on Big Five inventories.", "Ackerman et al. (2011)", STRONG),
        ({}, "Across people, higher totals on this test tend to go with higher Extraversion and lower Agreeableness on Big Five inventories.", "Paulhus & Williams (2002)", STRONG),
    ],
    "dass": [
        ({"Depression": H, "Anxiety": H}, "People with raised scores on both scales may also show higher Neuroticism on Big Five inventories, because the general distress the two scales share is closely tied to that trait. This test covers the past week, so the overlap is with a recent state and not a lasting trait.", "Clark & Watson (1991)", PARTIAL),
        ({"Depression": L, "Anxiety": L, "Stress": L}, "People with low scores on all three scales may also show lower Neuroticism on Big Five inventories. This test covers the past week, so the overlap is with a recent state and not a lasting trait.", "Clark & Watson (1991)", PARTIAL),
    ],
    "kims": [
        ({"Observing": H}, "People with higher Observing scores like this may also show higher Openness on Big Five inventories.", "Baer et al. (2004)", STRONG),
        ({"Describing": H}, "People with higher Describing scores like this may also score higher on measures of emotional intelligence, and lower on measures of difficulty identifying feelings.", "Baer et al. (2004)", STRONG),
        ({"Describing": L}, "People with lower Describing scores like this may also score higher on measures of difficulty identifying and describing feelings.", "Baer et al. (2004)", STRONG),
        ({"Accepting without Judgment": H}, "People with higher acceptance scores like this may also show lower Neuroticism on Big Five inventories.", "Baer et al. (2004)", STRONG),
        ({"Accepting without Judgment": L}, "People with lower acceptance scores like this may also show higher Neuroticism on Big Five inventories.", "Baer et al. (2004)", STRONG),
        ({"Acting with Awareness": H}, "People with higher awareness scores like this may also show lower Neuroticism and higher Conscientiousness on Big Five inventories.", "Baer et al. (2004)", STRONG),
    ],
    "hsq": [
        ({"Affiliative": H}, "People with higher affiliative humor like this may also show higher Extraversion and Openness on Big Five inventories.", "Martin et al. (2003)", STRONG),
        ({"Self-Enhancing": H}, "People with higher self-enhancing humor like this may also show higher Extraversion and lower Neuroticism on Big Five inventories.", "Martin et al. (2003)", STRONG),
        ({"Aggressive": H}, "People with higher aggressive humor like this may also show lower Agreeableness and lower Conscientiousness on Big Five inventories.", "Martin et al. (2003)", STRONG),
        ({"Self-Defeating": H}, "People with higher self-defeating humor like this may also show higher Neuroticism on Big Five inventories.", "Martin et al. (2003)", STRONG),
        ({"Affiliative": L}, "People with lower affiliative humor like this may also show lower Extraversion on Big Five inventories.", "Martin et al. (2003)", STRONG),
    ],
    "gcbs": [
        ({"Control of Information": H}, "People with higher scores like this may lean more on intuitive than analytic thinking on measures of thinking style.", "Swami et al. (2014)", STRONG),
        ({"Malevolent Global": H}, "People with higher scores like this may lean more on intuitive than analytic thinking on measures of thinking style.", "Swami et al. (2014)", STRONG),
        ({}, "Scores on tests like this one show almost no overlap with the Big Five. A meta-analysis found that none of the five traits was meaningfully related to conspiracy belief, so your result says little about what a personality inventory would show.", "Goreis & Voracek (2019)", STRONG),
    ],
    "riasec": [
        ({"Artistic": H}, "People with strong Artistic interests like this may also show higher Openness on Big Five inventories. It is the closest link between any interest type and any personality trait.", "Larson et al. (2002)", STRONG),
        ({"Investigative": H}, "People with strong Investigative interests like this may also show higher Openness on Big Five inventories.", "Larson et al. (2002)", STRONG),
        ({"Enterprising": H}, "People with strong Enterprising interests like this may also show higher Extraversion on Big Five inventories.", "Larson et al. (2002)", STRONG),
        ({"Social": H}, "People with strong Social interests like this may also show higher Extraversion and Agreeableness on Big Five inventories.", "Larson et al. (2002)", STRONG),
        ({"Conventional": H}, "People with strong Conventional interests like this may also show higher Conscientiousness on Big Five inventories.", "Larson et al. (2002)", STRONG),
        ({"Realistic": H}, "Realistic interests show little overlap with any Big Five trait, so a personality inventory would say little about this part of your profile.", "Larson et al. (2002)", STRONG),
    ],
    "attachment": [
        ({"Anxious": H}, "People with higher attachment anxiety like this may also show higher Neuroticism on Big Five inventories.", "Noftle & Shaver (2006)", STRONG),
        ({"Avoidant": H}, "People with higher attachment avoidance like this may also show lower Agreeableness and lower Extraversion on Big Five inventories.", "Noftle & Shaver (2006)", STRONG),
        ({"Anxious": L, "Avoidant": L}, "People with low anxiety and low avoidance like this may also show lower Neuroticism and higher Agreeableness on Big Five inventories.", "Noftle & Shaver (2006)", STRONG),
        ({}, "Attachment scores overlap with Big Five traits only in part, and they predict the quality of close relationships over and above those traits.", "Noftle & Shaver (2006)", STRONG),
    ],
    "fti": [
        ({"Explorer": H}, "People with higher Explorer scores like this may also show higher Openness and Extraversion on Big Five inventories.", "Fisher et al. (2015)", PARTIAL),
        ({"Builder": H}, "People with higher Builder scores like this may also show higher Conscientiousness on Big Five inventories.", "Fisher et al. (2015)", PARTIAL),
        ({"Negotiator": H}, "People with higher Negotiator scores like this may also show higher Agreeableness on Big Five inventories.", "Fisher et al. (2015)", PARTIAL),
        ({"Explorer": H, "Builder": L}, "People with this combination may show patterns also seen in people who score high on novelty seeking and low on harm avoidance in Cloninger's temperament model.", "Cloninger (1987)", PARTIAL),
        ({"Builder": H, "Explorer": L}, "People with this combination may show patterns also seen in people who score low on novelty seeking and high on harm avoidance in Cloninger's temperament model.", "Cloninger (1987)", PARTIAL),
    ],
}

MBTI: Dict[str, Dict[str, tuple]] = {
    "ambi": {
        "Extraversion": ("Extraversion (E)", "Introversion (I)"),
        "Openness": ("Intuition (N)", "Sensing (S)"),
        "Agreeableness": ("Feeling (F)", "Thinking (T)"),
        "Conscientiousness": ("Judging (J)", "Perceiving (P)"),
    },
    "hexaco": {
        "Extraversion": ("Extraversion (E)", "Introversion (I)"),
        "Openness": ("Intuition (N)", "Sensing (S)"),
        "Conscientiousness": ("Judging (J)", "Perceiving (P)"),
    },
}
MBTI_SOURCE = "McCrae & Costa (1989)"


def _cite(test_id: str, label: str) -> str:
    for paper in BIBLIOGRAPHY.get(test_id, []) + [p for papers in BIBLIOGRAPHY.values() for p in papers]:
        if _label(paper) == label:
            return paper["cite"]
    return EXTRA_SOURCES[label]


def _join(parts: List[str]) -> str:
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def _basis(when: Dict[str, str], pcts: Dict[str, int]) -> str:
    from ml.psych_layer import _ordinal

    if not when:
        return "Applies to everyone who takes this test"
    words = {H: "high", L: "low", M: "mid-range"}
    return "Shown because your " + " and ".join(
        f"{t} is {words[b]} ({_ordinal(pcts.get(t, 50))} percentile)" for t, b in when.items()
    )


def _pick(entries: List[tuple], bands: Dict[str, str], pcts: Dict[str, int], limit: int) -> List[tuple]:
    hits = [e for e in entries if all(bands.get(t) == b for t, b in e[0].items())]

    def weight(entry):
        when = entry[0]
        return (len(when), max(abs(pcts.get(t, 50) - 50) for t in when))

    specific = sorted([e for e in hits if e[0]], key=weight, reverse=True)
    general = [e for e in hits if not e[0]]
    keep = max(1, limit - 1) if general else limit
    chosen, seen = [], set()
    for entry in specific[:keep] + general:
        if len(chosen) >= limit or entry[1] in seen:
            continue
        seen.add(entry[1])
        chosen.append(entry)
    return chosen


def _mbti(test_id: str, bands: Dict[str, str]):
    mapping = MBTI.get(test_id)
    if not mapping:
        return None
    leans = [(hi if bands[t] == H else lo) for t, (hi, lo) in mapping.items() if bands.get(t) in (H, L)]
    mids = [t for t in mapping if bands.get(t) == M]
    if leans:
        text = f"People with trait levels like yours may show patterns also seen in people who report MBTI preferences for {_join(leans)}."
        if mids:
            text += f" Your {_join(mids)} {'is' if len(mids) == 1 else 'are'} mid-range, so there is no lean on the related {'preference' if len(mids) == 1 else 'preferences'}."
    else:
        text = "Your scores are mid-range on the traits that overlap with the MBTI, so people with a pattern like yours show no clear lean on any of its preferences."
    if test_id == "hexaco":
        text += " The link runs by way of the Big Five, whose Extraversion, Openness and Conscientiousness closely parallel the HEXACO factors of the same names."
    text += " This is a loose overlap between two different frameworks, and the MBTI has weaker research support than the test you took."
    return {"text": text, "source": MBTI_SOURCE, "basis": f"Based on your {_join(list(mapping))} scores",
            "personal": True, "backing": STRONG if test_id == "ambi" else PARTIAL}


def research_notes(test_id: str, pcts: Dict[str, int]) -> dict:
    from ml.psych_layer import _band

    bands = {t: _band(p) for t, p in pcts.items()}
    default = PARTIAL if test_id in PARTIAL_TESTS else STRONG
    facts = [{"text": text, "source": label, "basis": _basis(when, pcts), "personal": bool(when), "backing": default}
             for when, text, label in _pick(FACTS.get(test_id, []), bands, pcts, MAX_FACTS)]
    myths = [{"myth": myth, "truth": truth, "source": label, "basis": _basis(when, pcts), "personal": bool(when),
              "backing": default}
             for when, myth, truth, label in _pick(MYTHS.get(test_id, []), bands, pcts, MAX_MYTHS)]
    mbti = _mbti(test_id, bands)
    links = ([mbti] if mbti else []) + [
        {"text": text, "source": label, "basis": _basis(when, pcts), "personal": bool(when), "backing": backing}
        for when, text, label, backing in _pick(LINKS.get(test_id, []), bands, pcts, MAX_LINKS - (1 if mbti else 0))]
    labels = []
    for item in facts + myths + links:
        if item["source"] not in labels:
            labels.append(item["source"])
    return {"facts": facts, "myths": myths, "links": links, "sources": [_cite(test_id, label) for label in labels]}


def extra_authors() -> Dict[str, List[str]]:
    out = {}
    for test_id in BIBLIOGRAPHY:
        known = {_label(paper) for paper in BIBLIOGRAPHY[test_id]}
        labels = [entry[-1] for entry in FACTS.get(test_id, []) + MYTHS.get(test_id, [])]
        labels += [entry[2] for entry in LINKS.get(test_id, [])]
        if test_id in MBTI:
            labels.append(MBTI_SOURCE)
        seen = []
        for label in labels:
            if label in known:
                continue
            authors = _cite(test_id, label).split(" (", 1)[0].strip()
            if authors not in seen:
                seen.append(authors)
        out[test_id] = seen
    return out
