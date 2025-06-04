import streamlit as st
from chatbot import chatbot
from chatbot import system_prompt

# Sample card data for demonstration (replace with real data as needed)
cards = [
    {"name": "Barclaycard Rewards Mastercard", "desc": "Earn rewards on every purchase.", "img": "https://cards.barclaycardus.com/wp-content/uploads/2022/01/rewards-card.png"},
    {"name": "Barclaycard CashForward", "desc": "Unlimited 1.5% cash rewards.", "img": "https://cards.barclaycardus.com/wp-content/uploads/2022/01/cashforward-card.png"},
    {"name": "Barclaycard Arrival Plus", "desc": "Travel rewards and flexible redemption.", "img": "https://cards.barclaycardus.com/wp-content/uploads/2022/01/arrivalplus-card.png"},
]

def show_cards():
    cols = st.columns(3)
    for idx, card in enumerate(cards):
        with cols[idx % 3]:
            st.image(card["img"], width=200)
            st.subheader(card["name"])
            st.caption(card["desc"])
            col1, col2 = st.columns(2)
            with col1:
                st.button("Learn More", key=f"learn_{idx}")
            if idx == 0:  # Only show chat button for first card
                with col2:
                    if st.button("Chat with Us", key=f"chat_{idx}"):
                        st.session_state.page = "Chatbot"
                        st.rerun()

def show_chatbot():
    st.header("Credit Card Recommender Chatbot")
    st.write("Welcome! I will ask you for some details to assist you better.")
    
    # Initialize conversation and customer data states if not exists
    if "conversation" not in st.session_state:
        st.session_state.conversation = [{
            "role": "system",
            "content": system_prompt
        }]
    
    if "customer_data" not in st.session_state:
        st.session_state.customer_data = {
            "rewards_preference": "",
            "monthly_spend": "",
            "top_spending_categories": [],
            "interest_rate_importance": "",
            "balance_payment_habit": "",
            "late_payment_concern": "",
            "travel_frequency": "",
            "cobranded_preference": "",
            "annual_fee_preference": "",
            "priority_feature": ""
        }
    
    # Create two columns for chat and data display
    chat_col, data_col = st.columns([2, 1])
    
    with chat_col:
        # Scrollable chat history container
        st.markdown("""
            <style>
            .scrollable-chat-history {
                max-height: 50vh;
                overflow-y: auto;
                padding: 1em;
                background: #f8f9fa;
                border-radius: 8px;
                margin-bottom: 1em;
            }
            </style>
            <div class="scrollable-chat-history">
        """, unsafe_allow_html=True)
        
        for msg in st.session_state.conversation:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            elif msg["role"] == "assistant":
                st.markdown(f"**Chatbot:** {msg['content']}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Input always visible below chat history
        user_input = st.chat_input("Type your message...") if hasattr(st, "chat_input") else st.text_input("Type your message and press Enter:", key="chat_input")
        
        if user_input:
            st.session_state.conversation.append({"role": "user", "content": user_input})
            response, updated_conversation, updated_data = chatbot(user_input, st.session_state.conversation[:-1], st.session_state.customer_data)
            st.session_state.conversation = updated_conversation
            st.session_state.customer_data = updated_data
            st.rerun()
    
    with data_col:
        st.markdown("### Customer Preferences")
        st.json(st.session_state.customer_data)

def main():
    st.set_page_config(page_title="Barclaycard US", layout="wide")
    
    # Custom CSS to match Barclaycard's style
    st.markdown("""
        <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0;
        }
        .stButton button {
            background-color: #018fd0;
            color: white;
            border-radius: 20px;
            padding: 0.5rem 1.5rem;
            min-width: 120px;
        }
        .stButton button:hover {
            background-color: #0177ae;
        }
        .main-header {
            color: #00395d;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 2rem;
        }
        .card-container {
            display: flex;
            justify-content: space-between;
            margin: 2rem 0;
            gap: 2rem;
        }
        .card {
            flex: 1;
            padding: 1.5rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            text-align: center;
        }
        .card img {
            max-width: 100%;
            height: auto;
            margin-bottom: 1rem;
        }
        .footer {
            background-color: white;
            padding: 1rem 0;
            margin-top: 2rem;
            border-top: 1px solid #ddd;
        }
        .chat-container {
            margin-bottom: 120px;
            padding-bottom: 2rem;
        }
        .chat-input {
            margin-top: 2rem;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize page state if not exists
    if "page" not in st.session_state:
        st.session_state.page = "Home"
    
    # Top navigation bar
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.image("https://cards.barclaycardus.com/wp-content/themes/barclaycardus/assets/images/logo.svg", width=180)
    with col2:
        if st.button("Home"):
            st.session_state.page = "Home"
            st.rerun()
    with col3:
        if st.button("Credit Cards"):
            st.session_state.page = "Credit Cards"
            st.rerun()
    with col4:
        if st.button("Chat with Us"):
            st.session_state.page = "Chatbot"
            st.rerun()
    
    st.markdown("---")

    # Main content
    if st.session_state.page == "Home" or st.session_state.page == "Credit Cards":
        st.markdown('<h1 class="main-header">Welcome to Barclaycard US</h1>', unsafe_allow_html=True)
        st.write("Explore our range of credit cards and find the one that's right for you.")
        
        # Display cards in a grid
        col1, col2, col3 = st.columns(3)
        with col1:
            st.image(cards[0]["img"], width=250)
            st.subheader(cards[0]["name"])
            st.write(cards[0]["desc"])
            st.button("Learn More", key="learn_0")
            st.button("Chat with Us", key="chat_0", on_click=lambda: setattr(st.session_state, 'page', 'Chatbot'))
            
        with col2:
            st.image(cards[1]["img"], width=250)
            st.subheader(cards[1]["name"])
            st.write(cards[1]["desc"])
            st.button("Learn More", key="learn_1")
            
        with col3:
            st.image(cards[2]["img"], width=250)
            st.subheader(cards[2]["name"])
            st.write(cards[2]["desc"])
            st.button("Learn More", key="learn_2")
            
    elif st.session_state.page == "Chatbot":
        with st.container():
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            show_chatbot()
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown('<div class="footer">', unsafe_allow_html=True)
    footer_cols = st.columns(4)
    with footer_cols[0]:
        st.markdown("**Contact Us**")
        st.write("877-523-0478")
    with footer_cols[1]:
        st.markdown("**Security Center**")
    with footer_cols[2]:
        st.markdown("**FAQs**")
    with footer_cols[3]:
        st.markdown("© 2025 Barclays Bank Delaware, Member FDIC")
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()