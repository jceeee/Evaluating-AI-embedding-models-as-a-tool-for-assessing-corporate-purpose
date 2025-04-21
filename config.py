import os.path
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions

# config (the dot '.' is this folder where the script is executed)
folder = './.result'
folderResult = './.result/0Result'
chromePath = './chromedriver_linux64/chromedriver'

ai_rate_limit = 60  # rate limit for AI - csv is split into this number of rows
ai_token_limit = 8100  # ada-002 can only read 8191 *tokens* (1 token approx. 4 characters)
embedding_model = "text-embedding-ada-002"
os.environ["OPENAI_API_KEY"] = "YOUR-OPENAI-KEY"
TIMEOUT = 5

SEARCH_LOG_EVERY = 100  # how often search processes print progress
SEARCH_PROCESSES = 4  # use SEARCH_PROCESSES processors of CPU at the same time. If 0 use all

similarityBar = 0.796 #(for similarity every combination below 50%) #0.75 #(manual assessment)

# class for website data
class Website:
    name = ""  # name of the website e.g. 'Google'
    basePath = ""  # shortest path of the website e.g. 'https://google.com'
    firstPath = ""  # first path to visit on the website e.g. 'https://google.com'
    pathMustInclude = []  # all website paths must include this. Use for e.g. languages '/en-gb'
    pathMustNotInclude = []  # website paths must not include this. Use for e.g. excluding shops
    waitFunction = None

    def __init__(self, name, basePath, pathMustInclude, firstPath, pathMustNotInclude, waitFunction=None):
        self.name = name
        self.basePath = basePath
        self.pathMustInclude = pathMustInclude
        self.firstPath = firstPath
        self.pathMustNotInclude = pathMustNotInclude
        self.waitFunction = waitFunction


class SearchPrompt:
    name = ""  # name of prompt. Acts as folder name
    prompt = ""  # prompt
    embedding = []
    hitList = []

    def __init__(self, name, prompt):
        self.name = name
        self.prompt = prompt


# website data
websiteExcludeGlobal = ['facebook.com', 'instagram.com']
websites = [
 
    # Sonnentor
    Website('Sonnentor', 'https://www.sonnentor.com', ['sonnentor.com', '/en-gb/about-us'], 'https://www.sonnentor.com/en-gb/about-us', []),

    # Website('Example', 'https://example.com', ['example.com'], 'https://example.com', []),
]

# what to search for. No newlines in the text and every sentence should end with a dot.
searchPreserveCount = 5000  # do partial searches on websites and preserve best searchPreserveCount hits
searchResultCount = 100  # number of final result for each search

## long search promts (whole Hollensbe value definition)
searchPrompts = [
    SearchPrompt("Dignity", "Dignity - Viewing Each Person as a Someone, Not a Something. Leaders of the 'human relations' movement recognized the potential for viewing people not merely as useful instruments but as part of a social system (Mayo, 1933). Eighty years later, scholars and practitioners still wrestle with the challenge of integrating the 'whole' person at work. Recently, researchers have started to focus on the unhealthy and unfortunately prevalent picture of overworked employees who lead a 'divided life,' leaving their values and ideals at home when they go to work (Ramarajan & Reid, 2013). However, if employees' values are left at the doorway of their professional life, then the enterprise loses - and so does society. Said differently, each person deserves human dignity as a who, not a what, as a someone, not a something, yet much of the language of business subtly objectifies people generally as 'human capital' or 'human resources.' It follows that employers have a responsibility to be responsive, to treat people with respect and dignity, and to promote their fulfillment. Respecting the whole person includes thinking of people in all their various roles in relation to the business: as employees, customers, suppliers, investors, and citizens. Demonstrating respect means setting a purpose and seeking outcomes that enable people to reach their full potential. It means contributing fully to building relationships within the workplace and beyond that can ultimately engender trust between people and between business and society. As compelling examples of research along these lines, studies on compassion in leadership (Rynes et al., 2012), transformational leadership (Bono & Judge, 2003), and leading with meaning (Grant, 2012) have contributed to a dialogue among management scholars about valuing individuals and treating them with dignity. Yet, bringing human dignity front and center as part of purpose, or a business's reason for being, prompts additional questions for exploration. What can businesses do to create a purpose that helps employees reach their potential? How can organizations ensure people bring their whole selves to work? How can businesses address a mismatch between the care shown to employees and to other stakeholders, such as suppliers, in a way that supports their purpose?"),
    SearchPrompt("Solidarity", "Solidarity - Recognizing That Other People Matter. Recognizing that other people matter is part of solidarity, and can be summed up in a simple phrase: 'We are all in this together.' It means being in touch with the needs of communities, and, particularly, by looking for ways to help the under-privileged. Further, it involves being honest and fair with customers and suppliers and openly sharing information to enable them to make better informed choices. The market is not a value-free zone, and business can have a powerful impact in promoting and seeding stronger solidarity among people, or in undermining it. All human exchanges have a moral quality to them in that they can be respectful, or not, of the value of the other person. The attributes of a fair market free competition, plain dealing, honesty and openness on terms of trade, refusal to abuse a dominant position or asymmetry of knowledge to gain unfair advantage - all demand moral qualities of market participants. These are not normally adhered to, but simply assumed. Solidarity involves judging business actions as good, or not, in the context of the values, expectations, and needs of those with whom we seek to build relationships. This stands in contrast to operating in a self-interested, self-determined way that does not weigh sufficiently the impact of a business's actions. Opportunities to serve the broadest community reflect solidarity in action - by including the underserved, the underprivileged, and the disenfranchised. In this way, purpose can help bring people together, through providing new job opportunities, creating innovative goods and services, and serving new markets (e.g., George, McGahan, & Prabhu, 2012). Building recognition that other people matter into the fundamental purpose for business suggests new questions for research. How can businesses seek and provide access to opportunities to serve others? What are signs that a business has within its capabilities a purpose to serve others and lives it, and what factors influence its success in doing so?"),
    SearchPrompt("Plurality", "Plurality - Valuing Diversity and Building Bridges. Much has been written about diversity and the importance of building bridges across diverse cultures. As one example, Joshi and Roh (2009) analyze how context can set constraints and opportunities that affect the success of work team diversity on performance. Including plurality as a way to accomplish purpose would help ensure a context that minimizes constraints and creates opportunities for diversity. It would also ensure that diversity efforts in organizations do not occur in isolated silos, but are accepted as the way business is done. Increasing plurality to serve a broader purpose requires that leaders and managers be clear about who they are and what they stand for while being open to enrichment from others, valuing diversity of thinking and cultures. Plurality favors curiosity and inclusion over suspicion and the exclusion of those who think and act differently; it helps maintain consistency of purpose and values while encouraging responsiveness to people, markets, innovation, and growth. In a rapidly globalizing world, plurality provides a common currency for businesses to create a spirit of fraternity through clear, purpose-driven values that respect cultural differences, for which they are known to stand. The idea of embedding plurality in purpose is that we share a common humanity, and people are kept at the heart of the business enterprise. Purpose-driven values of plurality emphasize relationships among people rather than transactions. Emphasizing plurality based on purpose raises additional questions. For example, in practice, how do businesses operating across cultural differences seek to embody shared values? How do cultural differences affect the value placed on the individual and the importance of relationships within businesses? What factors engender lasting and trusted relationships over time within businesses, consonant with purpose? How do businesses combine the value of consistency of experience globally to the highest standard with respect for local practices, capabilities, insights, and traditions?"),
    SearchPrompt("Subsidiarity", "Subsidiarity - Exercising Freedom with Responsibility. Exercising freedom with responsibility relies on 'subsidiarity,' which, in this context, means promoting accountability at all levels by proper delegation of decision making -  based on the ability to make the 'right' decision rather than simply on hierarchy. Subsidiarity nurtures individuals and employees at all organizational levels who are able to contribute to decisions by speaking up and being heard (e.g., Burris, Detert, & Romney, 2013). Rather than creating dependency through reserving decisions for higher levels in the hierarchy, embedding subsidiarity in purpose would give employees the autonomy and support, when necessary, to make decisions that are purpose driven. As a result, employees would have a voice in their work, thus likely fostering innovation, creativity, and a sense of shared responsibility. Having a clear purpose that is understood and acted on across the company would give individuals across the company permission to say, 'No, that's not what we do,' when confronted with a situation that deviates from purpose. Subsidiarity requires an alignment of values across all levels of the organization, practices that are true to purpose, and giving voice to individuals. Person -  organization value congruence studies have shown us that transformational leadership relies on followers perceiving consistency between their own and the organization's values (e.g., Hoffman, By-num, Piccolo, & Sutton, 2011). Also, giving people the opportunity to have a voice is a well known tenet of justice theory. However, embedding subsidiarity into purpose would help normalize it in businesses, ensuring that people at all levels had the knowledge and voice to make the right decisions. Questions that arise from this theme include How does shared decision making based on purpose affect business outcomes? How do businesses create the alignment in purpose-driven values needed to give employees a voice in their work? What accountability measures can organizations use to ensure that freedom in decision making can be exercised with responsibility?"),
    SearchPrompt("Reciprocity", "Reciprocity - Building Trust and Trusted Relationships. Reciprocity is the basis for trust and trusted relationships. The values of reciprocity underlie the expectation that the conduct of business provides mutual benefit. The premise for reciprocity is honesty and integrity, such that individuals receive what they are entitled to or can reasonably expect from organizations. Further extensions of reciprocity would suggest that organizations leverage knowledge, resources, and capabilities to provide benefits that individuals and society desire and value, but cannot expect or demand. Reciprocity as an organizing value has received substantial attention in management research as intertwined with developing trust between employees and their supervisors (e.g., Wayne, Shore, & Liden, 1997) or across organizations (e.g., Gulati, 1995). The relationship between organizations and their customers is based on reciprocity and trust, where consumers expect value and satisfaction in the organization's products in return for their trust and loyalty (e.g., Sirdeshmukh, Singh, & Sabol, 2002). Reciprocity also implies responsibility - for example, Baer et al. (2015) find that being trusted can affect employees' emotional states. Considering reciprocity in light of organizational purpose could lead us to new research avenues.How do organizations perceive their contract with their local communities? Do employees feel that their physical and emotional effort in serving the organization is rightly rewarded or reciprocated? How does the organization deal with its supply chain partners in negotiating prices or sourcing materials? What gets contracted when a CEO joins or departs, and does it reflect contribution to both organizational purpose and actions that demonstrate the character traits that sustain purpose?"),
    SearchPrompt("Sustainability", "Sustainability - Being Stewards of People, Values, and Resources. The responsibilities of business extend to future generations, who will have the same rights as we do to use and enjoy the earth's resources. Sustainability means seeking to replace what we use and repair what we damage, striving to leave the planet in a better condition than that in which we found it. Many businesses take the responsibility of stewardship seriously; as corporate citizens, they care about their impact on the people they employ and the environment. They respect the rules demanded by society to regulate business and fair competition and innovation, and they promote and advocate more effective global action. However, this is not always the case - sometimes, with dramatic consequences for both the business and the environment. A challenge lies in embedding stewardship in purpose and acknowledging and seeking to measure the impact business has on people, values, resources, and the environment, as well as accepting responsibility for that impact. It involves taking steps to develop people, nurture values that support good stewardship, and actively preserve and restore existing resources and create new ones when possible so that others may enjoy their benefits. Management scholars have articulated how stewardship could be the guiding principle in organizations (e.g., Davis, Schoorman, & Donaldson, 1997). In a recent From the Editor on climate change (Howard-Grenville, Buckle, Hoskins, & George, 2014), questions facing scholars and practitioners were raised on organizational actions to adapt to climate change and environmental sustainability. However, framing stewardship as part of accomplishing business purpose would enable stakeholders to see how, through their commitment to the business's purpose, they can personally make a positive contribution to society - it would merit scrutiny and dialogue about the alignment of business practices and societal concerns. Stewardship in service to business purpose could generate questions about how business honors its duty to protect the natural world. How can businesses go about conserving and replacing finite resources in support of their purpose? How can organizations contribute to the communities in which they operate in ways that enable those communities to operate more effectively, prosper, and grow? In what ways can they self-regulate in areas such as product and service quality or environmental protection for the common good? And, importantly, how does an organization contribute to a better informed citizenship such that it can be sensibly challenged by society and aided in being true to purpose?"),
]
## short search promts (only headers Hollensbe value definition)
searchPrompts = [
    SearchPrompt("Dignity", "Dignity - Viewing Each Person as a Someone, Not a Something"),
    SearchPrompt("Solidarity", "Solidarity - Recognising That Other People Matter"),
    SearchPrompt("Plurality", "Plurality - Valuing Diversity and Building Bridges"),
    SearchPrompt("Subsidiarity", "Subsidiarity - Exercising Freedom with Responsibility"),
    SearchPrompt("Reciprocity", "Reciprocity - Building Trust and Trusted Relationships"),
    SearchPrompt("Sustainability", "Sustainability -  Being Stewards of People, Values, and Resources"),
]

## medium search promts (maximum 3 sentences)
searchPrompts = [
    SearchPrompt("Dignity", "Dignity -  Viewing Each Person as a Someone, Not a Something. This includes allowing employees to include personal values in their work and fostering them so that they can reach their full potential. Their definition includes not only employees but also suppliers, customers, investors, and other stakeholders. "),
    SearchPrompt("Solidarity", "Solidarity - Recognising That Other People Matter by looking for ways to help the underprivileged. This includes not abusing a dominant market position or insider knowledge and thus avoiding exploiting unfair advantages. An example of living Solidarity as a PDO is creating jobs for marginalised communities."),
    SearchPrompt("Plurality", "Plurality - Valuing Diversity and Building Bridges. This means that balancing purpose with diverse perspectives and cultures is also an important aspect for a PDO. Overall, openness and inclusiveness should be important for PDOs. "),
    SearchPrompt("Subsidiarity", "Subsidiarity - Exercising Freedom with Responsibility. This means promoting accountability at all levels by proper delegation of decision making based on the ability to make the ‘right’ decision rather than simply hierarchy. For this, employees need to be informed and educated about organisational goals and values so that they can make decisions without upper management. "),
    SearchPrompt("Reciprocity", "Reciprocity - Building Trust and Trusted Relationships with all stakeholders such as employees, customers, suppliers, and customers, but also competitors. This includes ensuring that customers receive value, building trust-based relationships with employees, fair negotiating practices with suppliers and also sharing knowledge with society and competitors to create value."),
    SearchPrompt("Sustainability", "Sustainability -  Being Stewards of People, Values, and Resources. This is mainly about pursuing sustainability in terms of the environment and climate change and also about informing and educating society about environmental stewardship so that companies can be held accountable. "),
]


# make sure folder names end with '/'
if folder[-1] != '/':
    folder += '/'
if folderResult[-1] != '/':
    folderResult += '/'

# create folders
if not os.path.exists(folder):
    os.mkdir(folder)
if not os.path.exists(folderResult):
    os.mkdir(folderResult)

# make sure website basePath does not end with '/'
for website in websites:
    if website.basePath[-1] == '/':
        website.basePath = website.basePath[0:-1]


# get saved website or make a request
def getFilename(websiteName, href, folderName, ending):
    global folder
    filename = href.replace('/', '_')
    filename = filename.replace('?', '_')
    if len(filename) + len(ending) > 255:
        filename = filename[:(255 - len(ending))]
    return os.path.join(folder, websiteName, folderName, filename + ending)
