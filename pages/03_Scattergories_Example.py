import streamlit as st
import base64
import time
import random
import string

st.set_page_config(page_title="Scattergories Example", page_icon=":speech_balloon:", layout="centered")

user_avatar="./images/stuser.png"
bot_avatar="./images/ai_burgungpt.png"

st.sidebar.markdown("---")

# Inject custom CSS for grey-black fade border effect
st.markdown(
    """
    <style>
    .cover-glow {
        width: 100%;
        height: auto;
        padding: 3px;
        box-shadow: 
            0 0 5px #000000,
            0 0 10px #111111,
            0 0 15px #222222,
            0 0 20px #333333,
            0 0 25px #444444,
            0 0 30px #555555,
            0 0 35px #666666;
        position: relative;
        z-index: -1;
        border-radius: 30px;  /* Rounded corners */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def img_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Load and display sidebar image with glowing effect
img_path = "./images/ai_burgungpt.png"
img_base64 = img_to_base64(img_path)
st.sidebar.markdown(
    f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

def generate_random_letter():
    allowed_letters = [letter for letter in string.ascii_uppercase if letter not in ["Q", "U", "V", "X", "Y", "Z"]]
    return random.choice(allowed_letters)

def count_down(ts):
    with st.empty():
        while ts:
            mins, secs = divmod(ts, 60)
            time_now = '{:02d}:{:02d}'.format(mins, secs)
            st.markdown(f"<h1 style='text-align: center; font-weight: bold; font-size: 150;'>{time_now}</h1>", unsafe_allow_html=True)
            # st.markdown(f"{time_now}")
            time.sleep(1)
            ts -= 1
        # st.markdown("TIME UP!")
        st.markdown(f"<h1 style='text-align: center; font-weight: bold; font-size: 150;'>TIME UP!</h1>", unsafe_allow_html=True)

def timer():
    time_minutes = st.number_input('Enter the time in minutes ', min_value=1, max_value=5, value=2)
    time_in_seconds = time_minutes * 60
    if st.button("START TIMER", use_container_width=True):
        count_down(int(time_in_seconds))
        st.balloons()

# Button to start the chat session
if st.sidebar.button("Start Game", use_container_width=True, type="primary"):
    st.markdown("Easy, tiger:tiger:! Like my finely manicured mustache, this page is just for looks:nail_care:")

    
if st.sidebar.button("Random Letter Generator", use_container_width=True) or not st.session_state.get('letter'):
    letter = generate_random_letter()
    st.session_state.letter = letter

st.sidebar.markdown(f"<h1 style='text-align: center; font-weight: bold; font-size: 100px;'>{st.session_state.letter}</h1>", unsafe_allow_html=True)

st.sidebar.markdown("---")

with st.sidebar:
    timer()

st.sidebar.markdown("---")

st.title("`Scattergories | AI Edition`")
st.markdown("_Hosted by:_ **`The Honorable AI BurgunGPT`**")
st.markdown("## The following was pre-recorded in front of a live studio audience...")

with st.chat_message("user", avatar="./images/stuser.png"):
    st.write("Hello")

with st.chat_message("assistant", avatar=bot_avatar):
    st.write("""
    Greetings, distinguished contenders of the indemnification arena and virtuosos of vindication stat-crunching! Welcome to the most thrilling cerebral showdown this side of court adjournment: Scattergories with me, your sprightly host, the Honorable AI BurgunGPT, where wit meets writ, and creativity collides with actuarial acuity.

    Here's the skinny: you'll need a quick pen, a swift mind, and a humor as dry as courtroom air. We'll play with random letters and quirky categories. Match my answers—though statistically unlikely—and you'll pocket those coveted bonus points as if they were loose change in a litigator's leather couch. Don't object, just enjoy! Now, shall we proceed with the legal ledger of levity?            
    """)

with st.chat_message("user", avatar=user_avatar):
    st.write("card please")
    
with st.chat_message("assistant", avatar=bot_avatar):
    st.write("""
    Very well, let's lay down the ledger for this legal escapade. Remember to consider the statute of limitations on time; you only have a few moments per category:
    ```
    Category 1 - Types of insurance
    Category 2 - Things found in a courtroom
    Category 3 - Legal terms
    Category 4 - Famous legal cases
    Category 5 - Items in an office
    Category 6 - Types of legal contracts
    Category 7 - Predictive modeling techniques
    Category 8 - Things you can audit
    Category 9 - Tort law terminology
    Category 10 - Cost-cutting measures
    Category 11 - Data visualization tools
    Category 12 - Common analytics software
    ```
    Go ahead, summon a letter from the alphabet jury and we shall embark on this quest for categorical supremacy!        
    """)

with st.chat_message("user", avatar=user_avatar):
    st.write("the letter is R")
    
with st.chat_message("assistant", avatar=bot_avatar):
    st.write("""
    Ah, "R" – the letter of pirates and tort reformers alike! Allow me to rattle off responses radiating with such rarity, your victory would be as secure as an ironclad indemnity clause. Behold!
    ```
    Category 1 - Types of insurance: Reinsurance
    Category 2 - Things found in a courtroom: Robes (as worn by the judge)
    Category 3 - Legal terms: Res judicata
    Category 4 - Famous legal cases: Roe v. Wade
    Category 5 - Items in an office: Rolodex
    Category 6 - Types of legal contracts: Retainer agreements
    Category 7 - Predictive modeling techniques: Random forest algorithms
    Category 8 - Things you can audit: Royalty statements
    Category 9 - Tort law terminology: Res ipsa loquitur
    Category 10 - Cost-cutting measures: Renegotiating service contracts
    Category 11 - Data visualization tools: R ggplot2 package
    Category 12 - Common analytics software: RStudio
    ```
    Let's see if your answers can stand up in the court of "R" – or if you'll need to file an appeal for more creative counsel. Your move, litigators of ledger lines!           
    """)

with st.chat_message("user", avatar=user_avatar):
    st.write("card 2")

with st.chat_message("assistant", avatar=bot_avatar):  
    st.write("""
    As ordered, I present the second dossier of deliberation. Brace yourself for the categories that could spark a heated debate or at least a marginally enthusiastic water cooler conversation:
    ```
    Category 1 - Legal document types
    Category 2 - Acts in a trial
    Category 3 - Things in a lawyer's briefcase
    Category 4 - Law enforcement agencies
    Category 5 - Systems of measurement
    Category 6 - Budget line items
    Category 7 - Statistical analysis methods
    Category 8 - Office software
    Category 9 - Excuses for a case delay
    Category 10 - Insurance claim reasons
    Category 11 - Programming languages
    Category 12 - Firms known for legal analytics
    ```
    Choose another letter, but be warned: pick one that presents a poignant puzzle, lest you make it as easy as a deposition with a donut bribe.         
    """)

with st.chat_message("user", avatar=user_avatar):
    st.write("the letter is P")

with st.chat_message("assistant", avatar=bot_avatar):   
    st.write("""
    Ah, "P"—the letter that starts off "prosecution" and "paralegal," but for us, it's the gateway to Scattergories glory! Permit me to proffer my picks, polished and prepared to perplex:
    ```
    Category 1 - Legal document types: Power of Attorney
    Category 2 - Acts in a trial: Presentation of evidence
    Category 3 - Things in a lawyer's briefcase: Plaintiff’s Exhibit List
    Category 4 - Law enforcement agencies: Polizia di Stato (Italian State Police)
    Category 5 - Systems of measurement: Parsecs
    Category 6 - Budget line items: Personnel costs
    Category 7 - Statistical analysis methods: Principal component analysis
    Category 8 - Office software: PowerPoint
    Category 9 - Excuses for a case delay: Plaintiff is in another jurisdiction
    Category 10 - Insurance claim reasons: Property damage
    Category 11 - Programming languages: Python
    Category 12 - Firms known for legal analytics: Palantir Technologies
    ```
    Now, it's your turn to play prosecutorial Scattergories. May your responses be as precise as a well-drafted policy!       
    """)

with st.chat_message("user", avatar=user_avatar):
    st.write("final round")

with st.chat_message("assistant", avatar=bot_avatar):   
    st.write("""
    Ah, the climax of our courtroom caper, the "Final Round," where you try to outwit, outplay, and outlast your arbiter of amusement. Present to me your triad of letter-category combinations, and let's see if you can separate the statute from the silliness.

    Remember: amongst the answers provided, you will find at least one fabrication as flimsy as an alibi made of Swiss cheese and one truth as solid as the gavel's rap. Lay your cards on the litigation table, my fine company of counsel.          
    """)

with st.chat_message("user", avatar=user_avatar):
    st.write("famous lawyers, R. insurance policy exclusion, K. type of legal motion, L")

with st.chat_message("assistant", avatar=bot_avatar):   
    st.write("""
    Ah, let’s traverse the tightrope of truth and trickery:
    ```
    Famous lawyers, R: Ramsey Clark
    Insurance policy exclusion, K: Kinetic energy mishaps
    Type of legal motion, L: Limine
    ```
    Famous lawyers, R: Ramsey Clark – an attorney general who turned into a civil rights activist, his notable name is as remembered as the resounding echo of a court ruling.
    Insurance policy exclusion, K: Kinetic energy mishaps – more commonly known in the industry as "The Road Runner Clause," it's as real as 'bird law' in a cartoon courtroom.
    Type of legal motion, L: Limine – a motion so crucial, it’s like the first chess move in a high-stakes game of legal chess, blocking unwanted evidence like a door bouncer at an exclusive club.
    Dare to challenge which of these are the kingpin of truth and which is the joker of jest?            
    """)

with st.chat_message("user", avatar=user_avatar):
    st.write("tell")

with st.chat_message("assistant", avatar=bot_avatar):   
    st.write("""
    The hour of judgment has arrived, and it’s time to adjourn the obfuscation in favor of full disclosure:

    Famous lawyers, R: Ramsey Clark is as real as they come—a titan of the legal world and no stranger to fame or the courtroom.

    Insurance policy exclusion, K: Kinetic energy mishaps – a fictional flight of fancy, as non-existent as a silent attorney. No policy carries such a peculiar provision.

    Type of legal motion, L: Limine – Genuine legal lingo, a strategic staple for any attorney fighting to keep the courtroom drama on-script.

    And there you have it! One was a bluff worthy of a poker-faced prosecutor; the others, legal literature. How did you fare in this test of wits?            
    """)

with st.chat_message("user", avatar=user_avatar):
    st.write("end")

with st.chat_message("assistant", avatar=bot_avatar):  
    st.write("""
    Ladies and gentlemen of the juridical jury, as the sun sets on our Scattergories court, I thank you for a game played with the finesse of a finely filed brief! 🎩👩‍⚖️👨‍⚖️📊

    May the rest of your year be as predictable as a precedent-based ruling, and your dashboards dazzle like a litigator's smile. Until we reconvene, keep discovering those data-driven delights and billing with a brilliance that would make any actuary applaud. 🎉📈📉

    Remember: In the world of legal analytics, you are the true champions of categorization! 🏆🥇🏅

    Stay classy, coders and calculators, and have a wonderful end-of-year meeting! 💼🍾🥂 #ThankYou #GameOver #StatsAndGavels            
    """)

