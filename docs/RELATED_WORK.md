# Related work: what is already known, and what this project adds

The literature check before the MPSA 2027 talk (TODO Nov 30, BACKLOG
"LITERATURE CHECK"). Its job: nothing gets presented as new that is not.
Citations only; no copyrighted PDFs are kept in the repo.

**How it was done (2026-11-14).** Two research passes, one per half of the
talk. Each was required to verify every work with a web search or a fetched
page (publisher, RePEc, NBER, PMC, arXiv, author page). The main citations
were then checked again by hand (marked ✔). Two claims did not survive that
check and are dropped (see "Corrections"). Works seen only through an
abstract are marked *(abstract)*.

---

## The one-line positioning

> Neighbour-to-neighbour diffusion, its decline since 1960, peer effects in
> rooftop solar, and the gap between issue votes and party votes are all
> established. What we add is one design (a discrete-time hazard with state
> clocks and a future-neighbour placebo) run the same way across laws,
> technology, names and political giving. With it we tell influence from
> look-alikes, and broadcasts from waves. We also add a county trait that
> crosses issues, forecast at county level, sealed in public before the vote
> and graded after.

---

## Part 1. Diffusion (the wave work)

### Each of our results against the literature

| Our result | Status | What to say |
|---|---|---|
| Neighbours adopt sooner, net of state clocks | **Established** (Walker 1969; Berry & Berry 1990) | It is the field's foundation; we use it, we did not find it |
| The neighbour pull fell after 1960 (~2.0 to ~1.4) | **Established** (Mallinson 2021 ✔; LaCombe, Tolbert & Mossberger 2022; DellaVigna & Kim 2026 ✔) | Our number agrees with theirs; it is a replication, not a discovery |
| Model-legislation laws spread less along borders | Consistent with Garrett & Jansa 2015 | Cite them |
| Hot-topic laws spread less along borders | Consistent with morality-policy and partisan-diffusion work (Boushey 2010; DellaVigna & Kim) | Cite them |
| Peer effects in rooftop solar | **Established** (Bollinger & Gillingham 2012 ✔; Graziano & Gillingham 2015; Rode & Weber 2016; Bollinger et al. 2022) | Solar is the *calibration* wave, a known effect the method must recover, not a finding |
| Programmes can make clusters (Illinois Shines) | Known (Gillingham & Bollinger 2021: Solarize campaigns cause local clusters) | Our Illinois case is a good illustration, not a claim |
| Past-vs-next neighbour placebo in a hazard model | **New application of a known logic.** Related: shuffle and edge-reversal tests (Anagnostopoulos et al. 2008), negative controls (Egami; Egami & Tchetgen Tchetgen), placebo policies (DellaVigna & Kim) | Present it as a bound under a stated assumption (similarity is symmetric in time), not as identification. Address Shalizi & Thomas 2011 by name. Read Egami before claiming novelty |
| Baby names spread state to state (~10x) | **Partly new.** Neighbouring states share naming patterns (Barucca et al. 2015); names rise and fall (Berger & Le Mens 2009) | No hazard model of name take-off with a neighbour term found. Check Goldenberg & Levy 2009, who argue proximity *rose* with the internet |
| "Shared roads" across idea families (laws vs names ~0.3) | **New as far as found.** Within policies, persistent pathways exist (Desmarais, Harden & Boehmke 2015) | Cite Desmarais et al. as the within-policy precedent |
| Giving after a news shock is a same-day broadcast; a new candidate's donors spread modestly | **Partly new.** Broadcast vs imitation is Bass's p vs q (1969); giving clusters in space (Gimpel, Lee & Kaminski 2006; Cho 2003; Cho & Gimpel 2007); small donors surge after events (Bouton et al.) | No study found contrasting broadcast and neighbour spread in giving at daily ZIP/county resolution with a past/next placebo |
| Hand-offs vs an exact within-state shuffle; "real in the model, at chance on the map" | **New as far as found** (shuffle nulls exist: Anagnostopoulos et al. 2008) | A presentation device more than a research claim |

### Verified works, by strand

**Policy diffusion and event history**
- Walker, J.L. (1969). "The Diffusion of Innovations among the American States." *APSR* 63(3):880-899. doi:10.2307/1954434. Founding paper: regional pioneers, followed by neighbours.
- Berry, F.S. & Berry, W.D. (1990). "State Lottery Adoptions as Policy Innovations: An Event History Analysis." *APSR* 84(2):395-415. doi:10.2307/1963526. Brought discrete-time event history, with a neighbour-adoption term, into the field.
- Mooney, C.Z. (2001). "Modeling Regional Effects on State Policy Diffusion." *Political Research Quarterly* 54(1):103-124. doi:10.1177/106591290105400106. The regional effect is not constant over a diffusion.
- Berry, W.D. & Baybeck, B. (2005). "Using Geographic Information Systems to Study Interstate Competition." *APSR* 99(4):505-519. Separates competition from learning using where residents live.
- Shipan, C.R. & Volden, C. (2008). "The Mechanisms of Policy Diffusion." *AJPS* 52(4):840-857. doi:10.1111/j.1540-5907.2008.00346.x. Learning, competition, imitation, coercion.
- Volden, C., Ting, M.M. & Carpenter, D.P. (2008). "A Formal Model of Learning and Policy Diffusion." *APSR* 102(3):319-332. doi:10.1017/S0003055408080271. Much apparent diffusion could be similar governments acting alone: the "just alike" problem our placebo targets.
- Gilardi, F. (2010). "Who Learns from What in Policy Diffusion Processes?" *AJPS* 54(3):650-666.
- Boushey, G. (2010). *Policy Diffusion Dynamics in America.* Cambridge University Press. Diffusion comes in outbreaks; morality policies differ.
- Shipan, C.R. & Volden, C. (2012). "Policy Diffusion: Seven Lessons for Scholars and Practitioners." *Public Administration Review* 72(6):788-796.
- Desmarais, B.A., Harden, J.J. & Boehmke, F.J. (2015). "Persistent Policy Pathways: Inferring Diffusion Networks in the American States." *APSR* 109(2):392-406. doi:10.1017/S0003055415000040.
- Garrett, K.N. & Jansa, J.M. (2015). "Interest Group Influence in Policy Diffusion Networks." *State Politics & Policy Quarterly* 15(3):387-417. Model legislation routes around geography.
- Mallinson, D.J. (2016). "Building a Better Speed Trap." *SPPQ* 16(1):98-120. doi:10.1177/1532440015596088. *(abstract)*
- ✔ Boehmke, F.J., Brockway, M., Desmarais, B.A., Harden, J.J., LaCombe, S., Linder, F. & Wallach, H. (2020). "SPID: A New Database for Inferring Public Policy Innovativeness and Diffusion Networks." *Policy Studies Journal* 48(2):517-545. doi:10.1111/psj.12357. The data we use (the Dataverse release credits Boehmke, LaCombe and Brockway; `docs/DATA_SOURCES.md`).
- ✔ Mallinson, D.J. (2021). "Who Are Your Neighbors? The Role of Ideology and Decline of Geographic Proximity in the Diffusion of Policy Innovations." *Policy Studies Journal* 49(1):67-88. doi:10.1111/psj.12351. 556 policies, 1960-2014: contiguous neighbours matter less over time; ideological similarity stays.
- LaCombe, S., Tolbert, C. & Mossberger, K. (2022). "Information and Policy Innovation in U.S. States." *Political Research Quarterly* 75(2):353-365. More broadband, less reliance on neighbours.
- ✔ DellaVigna, S. & Kim, W. (2026). "Policy Diffusion and Polarization across U.S. States." *Review of Economic Studies* 93(3):1602-1634. doi:10.1093/restud/rdaf070 (NBER WP 30142). Proximity best predicts adoption 1950-2000; party alignment since 2000.

**Rooftop solar**
- ✔ Bollinger, B. & Gillingham, K. (2012). "Peer Effects in the Diffusion of Solar Photovoltaic Panels." *Marketing Science* 31(6):900-912. doi:10.1287/mksc.1120.0727. California, ZIP by quarter.
- Graziano, M. & Gillingham, K. (2015). "Spatial Patterns of Solar Photovoltaic System Adoption." *Journal of Economic Geography* 15(4):815-839. Connecticut: wave-like spread from centres; decays with distance and time.
- Rode, J. & Weber, A. (2016). "Does Localized Imitation Drive Technology Adoption?" *Journal of Environmental Economics and Management* 78:38-48. doi:10.1016/j.jeem.2016.02.001. Germany: imitation is strongly local.
- Gillingham, K. & Bollinger, B. (2021). "Social Learning and Solar Photovoltaic Adoption." *Management Science* 67(11):7091-7112. doi:10.1287/mnsc.2020.3840. Programmes manufacture clusters.
- Bollinger, B., Gillingham, K., Kirkpatrick, A.J. & Sexton, S. (2022). "Visibility and Peer Influence in Durable Good Adoption." *Marketing Science* 41(3):453-476. doi:10.1287/mksc.2021.1306. Visible panels drive neighbours.

**Names**
- Berger, J. & Le Mens, G. (2009). "How Adoption Speed Affects the Abandonment of Cultural Tastes." *PNAS* 106(20):8146-8150. doi:10.1073/pnas.0812647106.
- Bentley, R.A. & Ormerod, P. (2012). "Accelerated Innovation and Increased Spatial Diversity of US Popular Culture." *Advances in Complex Systems* 15.
- Barucca, P., Rocchi, J., Marinari, E., Parisi, G. & Ricci-Tersenghi, F. (2015). "Cross-correlations of American Baby Names." *PNAS* 112(26):7943-7947. doi:10.1073/pnas.1507143112.

**Political geography and giving**
- Cho, W.K.T. (2003). "Contagion Effects and Ethnic Contribution Networks." *AJPS* 47(2):368-387. doi:10.1111/1540-5907.00026.
- Gimpel, J.G., Lee, F.E. & Kaminski, J. (2006). "The Political Geography of Campaign Contributions in American Politics." *Journal of Politics* 68(3):626-639.
- Cho, W.K.T., Gimpel, J.G. & Dyck, J.J. (2006). "Residential Concentration, Political Socialization, and Voter Turnout." *Journal of Politics* 68(1):156-167.
- Cho, W.K.T. & Gimpel, J.G. (2007). "Prospecting for (Campaign) Gold." *AJPS* 51(2):255-268.
- Cho, W.K.T. & Rudolph, T.J. (2008). "Emanating Political Participation." *British Journal of Political Science* 38(2):273-289. doi:10.1017/S0007123408000148.
- Gimpel, J.G., Karnes, K.A., McTague, J. & Pearson-Merkowitz, S. (2008). "Distance-decay in the Political Geography of Friends-and-Neighbors Voting." *Political Geography* 27(2):231-252. doi:10.1016/j.polgeo.2007.10.005.
- Meredith, M. (2013). "Exploiting Friends-and-Neighbors to Estimate Coattail Effects." *APSR* 107(4):742-765.
- Traag, V.A. (2016). "Complex Contagion of Campaign Donations." *PLOS ONE* 11(4):e0153539. doi:10.1371/journal.pone.0153539. Spread through an elite social network, not geography.
- Bouton, L., Cagé, J., Dewitte, E. & Pons, V. "Small Campaign Donors." NBER WP 30050 (2022, rev. 2024). Small donors respond to prominence and ads; giving surges right after events.

**Methods: influence vs look-alikes; spatial diffusion**
- Hägerstrand, T. (1967). *Innovation Diffusion as a Spatial Process.* University of Chicago Press.
- Bass, F.M. (1969). "A New Product Growth for Model Consumer Durables." *Management Science* 15(5):215-227. doi:10.1287/mnsc.15.5.215. External (broadcast) vs internal (imitation) adoption.
- Manski, C.F. (1993). "Identification of Endogenous Social Effects: The Reflection Problem." *Review of Economic Studies* 60(3):531-542.
- Christakis, N.A. & Fowler, J.H. (2007). "The Spread of Obesity in a Large Social Network over 32 Years." *NEJM* 357(4):370-379. Note: no effect among geographic neighbours.
- Lyons, R. (2011). "The Spread of Evidence-Poor Medicine via Flawed Social-Network Analysis." *Statistics, Politics, and Policy* 2(1). doi:10.2202/2151-7509.1024.
- Anagnostopoulos, A., Kumar, R. & Mahdian, M. (2008). "Influence and Correlation in Social Networks." *KDD 2008*, 7-15. The shuffle test.
- Aral, S., Muchnik, L. & Sundararajan, A. (2009). "Distinguishing Influence-based Contagion from Homophily-driven Diffusion in Dynamic Networks." *PNAS* 106(51):21544-21549.
- Shalizi, C.R. & Thomas, A.C. (2011). "Homophily and Contagion Are Generically Confounded in Observational Social Network Studies." *Sociological Methods & Research* 40(2):211-239. doi:10.1177/0049124111404820. **The critique our placebo must answer.**
- Egami, N. "Identification of Causal Diffusion Effects Under Structural Stationarity." arXiv:1810.07858. *(abstract)* Spatial hate-crime diffusion; earlier estimates overstated.
- Egami, N. & Tchetgen Tchetgen, E. "Identification and Estimation of Causal Peer Effects Using Double Negative Controls for Unmeasured Network Confounding." *JRSS-B*, doi:10.1093/jrsssb/qkad132.
- Hui, I. & Cho, W.K.T. (2017). "Spatial Dimensions of American Politics." **A book chapter** (volume not yet confirmed), not a journal article. Our `docs/spdim.pdf` copy stays uncommitted (copyright).

---

## Part 2. Ballot measures, county opinion and forecasting (the False Bastion work)

### Each of our claims against the literature

| Our claim | Status | What to say |
|---|---|---|
| Issue votes diverge from party votes (the "False Bastion" gap) | **Established** (Amos & Middlewood 2024; Gardner, McCrary & Spencer 2025 and working paper 2026; Kuriwaki on ticket splitting; Warshaw & Rodden 2012; Lax & Phillips). In Missouri, Casey & Strunc 2026 ✔ already name "ballot measure ticket splitting" | The gap is known; "False Bastion" is our name for it, not a discovery |
| The partisanship-controlled residual is a stable county trait across *different* issues (Ohio 0.62; MO abortion vs minimum wage +0.52; minimum wage 2018 vs 2024 +0.68) | **Partly new.** Places scaled from many referendums are stable and multidimensional (Swiss municipal work; Leemann, Emmenegger & Walter 2025; Gerber & Lewis 2004; Snyder 2005); individual-level analogue in Ansolabehere, Rodden & Snyder 2008 | New as far as found: a US county residual net of partisanship that holds across post-Dobbs issues and years. Address Kendall & Matsusaka's "common good" voting as a rival explanation |
| Minimum wage crosses party most in poor red states | **Consistent with known work**, not a reversal of it: Bartels 2006 and Gelman et al. 2007 already rebutted *What's the Matter with Kansas?* with surveys | Say "county and state ballot evidence that agrees with Bartels and Gelman et al.", not "inverts" (corrected 2026-11-14) |
| The residual carries between general elections but not primary to general (+0.47 vs +0.06) | **Partly new** (Amos & Middlewood show Kansas's August electorate differed) | No study found of how the residual carries over between electorates |
| County-level ballot-measure forecast, hash-sealed before the vote, scored after certification | **New as far as found.** Precedents: pre-registration in political science (Monogan 2013); published-then-judged forecasts (*PS* symposia, national/state candidate races) | The strongest claim to make |
| Forecast on partisanship + prior residual, not demographics | Supported by ✔ Calvo, Pons & Shapiro (NBER WP 33016): demographic forecasts since 1952 did worse than a 50-50 guess | Cite as the reason for the design |
| Persuade / turn out / skip labels | **Established campaign practice** (Nickerson & Rogers 2014; Hersh 2015; Hillygus & Shields 2008) | Possibly new: deriving them from a forecast, graded county trait. Caution: general-election persuasion averages ~0 (Kalla & Broockman 2018); county labels risk the ecological fallacy |
| County ideal points x measure cutpoints (measurement design) | **Method established** (Gerber & Lewis 2004; Snyder 2005; Lewis 2001; Puglisi & Snyder; Swiss scaling) | New would be the application: multi-state US county panels bridged by overlapping measures, used ex ante |

### Verified works, by strand

**Issue vs party votes; ticket splitting**
- Amos, B. & Middlewood, A.T. (2024). On the Kansas August 2022 abortion amendment. *American Politics Research* 52(5):534-545. doi:10.1177/1532673X241263089. A significant minority of Republicans voted against; an unusual primary electorate.
- Gardner, G., McCrary, K. & Spencer, M.K. (2025). "Abortion ballot measures affect election outcomes." *Economics Letters*. 2022 measures cut the Republican margin.
- Gardner, McCrary & Spencer (working paper, 2026). "Direct Democracy and Candidate Choice: Evidence from Abortion Ballot Measures." melissakspencer.com/ABM.pdf. 16 measures; moderates vote the measure, then choose candidates on other issues.
- Kuriwaki, S. (2025/26). "Ticket Splitting in a Nationalized Era." *Journal of Politics*. doi:10.1086/734263.
- ✔ Casey, K.L. & Strunc, A. (2026). "Are Missourians Voting for Conservative Candidates and Liberal Policies? A Case for Ballot Measure Ticket Splitting." *Missouri Policy Journal* 2(3). 475-person 2024 exit poll in Maryville, MO.
- Lupia, A. (1994). "Shortcuts Versus Encyclopedias." *APSR* 88(1):63-76.
- Bowler, S. & Donovan, T. (1998). *Demanding Choices: Opinion, Voting, and Direct Democracy.* University of Michigan Press.

**Opinion vs policy; small-area opinion**
- Lax, J.R. & Phillips, J.H. (2009). "How Should We Estimate Public Opinion in the States?" *AJPS* 53(1):107-121.
- Lax, J.R. & Phillips, J.H. (2009). "Gay Rights in the States: Public Opinion and Policy Responsiveness." *APSR* 103(3):367-386.
- Lax, J.R. & Phillips, J.H. (2012). "The Democratic Deficit in the States." *AJPS* 56(1):148-166. Policy matches majority opinion about half the time.
- Warshaw, C. & Rodden, J. (2012). "How Should We Measure District-Level Public Opinion on Individual Issues?" *Journal of Politics* 74(1):203-219. Presidential vote is a poor stand-in for issue opinion.
- Gelman, A., Shor, B., Bafumi, J. & Park, D. (2007). "Rich State, Poor State, Red State, Blue State." *QJPS* 2(4):345-367.
- Bartels, L. (2006). "What's the Matter with What's the Matter with Kansas?" *QJPS* 1(2):201-226.
- Ansolabehere, S., Rodden, J. & Snyder, J.M. (2008). "The Strength of Issues." *APSR* 102(2):215-232. *(abstract)*

**Scaling ballot measures; places as ideal points**
- Gerber, E.R. & Lewis, J.B. (2004). "Beyond the Median." *Journal of Political Economy* 112(6):1364-1383.
- Lewis, J.B. (2001). "Estimating Voter Preference Distributions from Individual-Level Voting Data." *Political Analysis* 9(3):275-297.
- Snyder, J.M. Jr. (2005, working note). "Estimating the Distribution of Voter Preferences Using Partially Aggregated Voting Data." Essentially our county-ideal-point x cutpoint idea.
- Puglisi, R. & Snyder, J.M. (2011). "The Balanced US Press." NBER WP 17263. Bridging actors on one scale.
- Kendall, C. & Matsusaka, J.G. "The Common Good and Voter Polarization." SSRN doi:10.2139/ssrn.3868589. A rival, non-ideological explanation for crossing party.
- Leemann, L. & Wasserfallen, F. (2016). "The Democratic Effect of Direct Democracy." *APSR* 110(4):750-762.
- Leemann, L., Emmenegger, P. & Walter, A. (2025). "Vox Populi: Popular Support for the Popular Initiative." *APSR* 119(4):1777-1791. Municipality ideal points from Swiss returns.

**Forecasting and pre-registration**
- Monogan, J.E. III (2013). "A Case for Registering Studies of Political Outcomes." *Political Analysis* 21:21-37.
- Mongrain, P. & Stegmaier, M. (2025). "Introduction to Forecasting the 2024 US Elections." *PS* 58(2). doi:10.1017/S1049096524001008.
- ✔ Calvo, R., Pons, V. & Shapiro, J.M. (2024). "Pitfalls of Demographic Forecasts of US Elections." NBER WP 33016.

**Targeting**
- Gerber, A.S. & Green, D.P. (2000). "The Effects of Canvassing, Telephone Calls, and Direct Mail on Voter Turnout." *APSR* 94(3):653-663.
- Kalla, J. & Broockman, D. (2018). "The Minimal Persuasive Effects of Campaign Contact in General Elections." *APSR* 112(1):148-166.
- Nickerson, D.W. & Rogers, T. (2014). "Political Campaigns and Big Data." *Journal of Economic Perspectives* 28(2):51-74. doi:10.1257/jep.28.2.51.
- Hersh, E. (2015). *Hacking the Electorate.* Cambridge University Press.
- Hillygus, D.S. & Shields, T. (2008). *The Persuadable Voter.* Princeton University Press. Cross-pressured partisans: the individual-level twin of a False Bastion.

**A gap worth saying out loud:** no peer-reviewed county- or precinct-level
study was found for Kentucky 2022, Michigan 2022, Ohio 2023, or the 2024
minimum-wage measures.

---

## Corrections made during the check

- **"Inverts *What's the Matter with Kansas?*"** overclaimed; Bartels (2006)
  and Gelman et al. (2007) already made that argument. Reworded in
  `docs/FINDINGS.md` and the blueprint page (2026-11-14). The executed
  notebook `minimum_wage_economic_bastions` keeps its original wording as a
  dated record; read it with this correction.
- **The post-1960 decline in neighbour pull** is a replication of Mallinson
  (2021) and DellaVigna & Kim (2026), not a discovery. The research log says
  so.
- **Dropped:** "Hanretty (2017) published local estimates before the Brexit
  vote and scored them." The paper (*JEPOP* 27(4)) remaps results to
  constituencies after the vote; it is not a forecast precedent.
- **Dropped:** a "62% of straight-ticket Republicans" figure attributed to
  Casey & Strunc; it could not be found on the paper's page. The concept is
  cited; the number is not.

## Still to read or confirm

- **Egami (arXiv:1810.07858):** does its placebo use future-neighbour outcomes? Read it before calling our past-vs-next placebo a new application.
- **Goldenberg & Levy (2009), "Distance Is Not Dead"** (arXiv 0906.3202): geographic proximity in name spread *rose* in the internet era, which cuts against our "fading".
- **The book that contains Hui & Cho (2017).**
- **Sebold, Dowdle, Limbocker & Stewart** (SSRN 1901546), the timing and geography of early presidential money: read it.
- **Not yet searched:**
  - Volden 2006 ("States as Policy Laboratories")
  - Nicholson-Crotty 2009
  - Hays, Kachi & Franzese 2010 (spatial-temporal models)
  - Lieberson 2000 (*A Matter of Taste*)
- **Key, V.O. (1949), *Southern Politics*:** confirmed only through Meredith's citation.
- **Final journal venues:** Puglisi & Snyder; Kendall & Matsusaka.
