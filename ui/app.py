import streamlit as st
import requests
import json
import uuid
import binascii
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import ed25519
from streamlit_autorefresh import st_autorefresh


# --- UI CONFIGURATION AND STYLING ---
st.set_page_config(page_title="Blockchain Observer", page_icon="🔗", layout="wide")

# Custom CSS for premium Glassmorphism Dark Mode
st.markdown(
    """
<style>
/* Base Theme overrides */
html, body, [class*="css"] {
    font-family: 'Inter', 'Roboto', sans-serif;
    background-color: #0d1117;
    color: #e6edf3;
}

/* Glassmorphism Cards */
.stCard, .stExpander, div[data-testid="stMetric"] {
    background: rgba(22, 27, 34, 0.7) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(0,0,0,0.4) !important;
}

/* Gradients for metric values */
div[data-testid="stMetricValue"] {
    background: linear-gradient(90deg, #58a6ff, #bc8cff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
}

/* Forms and Inputs */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background-color: rgba(30, 36, 45, 0.8) !important;
    color: #c9d1d9 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
    border: 1px solid #58a6ff !important;
    box-shadow: 0 0 5px rgba(88, 166, 255, 0.5) !important;
}

/* Gradient Buttons */
div.stButton > button:first-child {
    background: linear-gradient(90deg, #1f6feb 0%, #238636 100%) !important;
    border: none !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 10px rgba(31, 111, 235, 0.3) !important;
}
div.stButton > button:first-child:hover {
    box-shadow: 0 6px 15px rgba(31, 111, 235, 0.5) !important;
    transform: scale(1.02);
}

/* Headers */
h1 {
    background: linear-gradient(135deg, #79c0ff 0%, #d2a8ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
}
h2, h3 {
    color: #e6edf3 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# --- NODE CONFIGURATION ---
NODES = {
    "Node 1 (Port 8001)": "http://localhost:8001",
    "Node 2 (Port 8002)": "http://localhost:8002",
    "Node 3 (Port 8003)": "http://localhost:8003",
}


# --- HELPER FUNCTIONS ---
def get_blocks(url: str):
    try:
        response = requests.get(f"{url}/blocks", timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None


def send_transaction(url: str, tx_dict: dict):
    try:
        response = requests.post(f"{url}/transactions", json=tx_dict, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to send transaction: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                st.error(f"Server response: {e.response.json()}")
            except Exception:
                pass
        return None


def sign_transaction(payload: dict, private_key_hex: str) -> dict | None:
    tx_id = str(uuid.uuid4())
    timestamp_str = str(datetime.now())

    signable_dict = {
        "id": tx_id,
        "timestamp": timestamp_str,
        "payload": payload,
    }
    data_to_sign = json.dumps(signable_dict, sort_keys=True).encode()

    try:
        private_key_bytes = bytes.fromhex(private_key_hex.strip())
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        signature = private_key.sign(data_to_sign)
        signature_hex = binascii.hexlify(signature).decode()

        signable_dict["signature"] = signature_hex
        return signable_dict
    except Exception as e:
        st.error(f"Error generating signature: {e}")
        return None


# --- MAIN UI ---
st.title("🌐 Multi-Node Certificate Blockchain Explorer")

tab1, tab2, tab3 = st.tabs(["📊 Ledger Visualization", "Send Transaction", "🛠️ Simulate Block"])

# --- TAB 1: LEDGER VISUALIZATION ---
with tab1:
    st.header("Node Ledger States")
    
    auto_refresh = st.checkbox("Auto-refresh Ledger (every 5s)", value=True)
    if auto_refresh:
        st_autorefresh(interval=5000, limit=None, key="ledger_autorefresh")
        
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for i, (name, url) in enumerate(NODES.items()):
        blocks = get_blocks(url)
        with cols[i]:
            st.subheader(name)
            if blocks is None:
                st.error("⚠️ Offline")
            else:
                st.metric("Total Blocks", len(blocks))

                with st.expander("View Data", expanded=True):
                    for idx, block in enumerate(reversed(blocks)):
                        st.markdown(f"**Block {block.get('index')}**")
                        st.code(json.dumps(block, indent=2), language="json")


# --- TAB 2: SEND TRANSACTION ---
with tab2:
    st.header("Issue New Certificate")
    st.markdown("Create a transaction and sign it using your Ed25519 private key.")

    colA, colB = st.columns([1, 1])

    with colA:
        st.subheader("Certificate Details")
        person_name = st.text_input("Student Name", placeholder="Kiev Lima")
        person_email = st.text_input("Student Email", placeholder="kiev@example.com")
        course = st.text_input("Course Name", placeholder="Sistemas Distribuídos")
        certification_date = st.date_input("Certification Date")
        institution = st.text_input("Institution", placeholder="UFRN")

    with colB:
        st.subheader("Wallet & Submission")
        target_node = st.selectbox("Select Target Node", list(NODES.keys()))
        private_key = st.text_input(
            "Private Key (Hex format)",
            type="password",
            help="The 64-character hex string generated by generate_keys.py",
        )

        submit = st.button("Sign and Send Transaction 🚀", use_container_width=True)

        if submit:
            if not private_key:
                st.error("Private Key is required to sign the transaction.")
            elif not all([person_name, person_email, course, institution]):
                st.error("All Fields are required!")
            else:
                payload = {
                    "person_name": person_name,
                    "person_email": person_email,
                    "course": course,
                    "certification_date": str(certification_date),
                    "institution": institution,
                }

                # Sign transaction
                with st.spinner("Signing..."):
                    tx_dict = sign_transaction(payload, private_key)

                if tx_dict:
                    # Send to target node
                    node_url = NODES[target_node]
                    with st.spinner(f"Broadcasting to {target_node}..."):
                        result = send_transaction(node_url, tx_dict)

# --- TAB 3: SIMULATE ATTACK ---
with tab3:
    st.header("Simulate Attack (Direct Block Injection)")
    st.markdown("Create a valid block with random transactions to test if the node accepts it. The UI acts as a malicious miner, signs fake transactions, calculates the Proof of Work, and injects the block directly.")
    
    col_target, col_empty = st.columns([1, 1])
    with col_target:
        target_node_block = st.selectbox("Select Target Node for Attack", list(NODES.keys()), key="simulate_attack_target")
        private_key = st.text_input("Attacker Private Key (Hex)", type="password", help="Required to sign the injected fake transactions")
        num_transactions = st.number_input("Number of Fake TXs", min_value=1, max_value=10, value=2)
    
    if st.button("Generate, Mine & Inject Block 💥", use_container_width=True):
        if not private_key:
            st.error("Private Key is required to sign the fake transactions! (Use the same generated key for the system)")
        else:
            node_url = NODES[target_node_block]
            
            with st.spinner("Fetching current chain state..."):
                blocks = get_blocks(node_url)
                
            if blocks is None:
                st.error("Target node is offline or unreachable.")
            else:
                last_block = blocks[-1] if blocks else None
                index = last_block["index"] + 1 if last_block else 1
                previous_hash = last_block["hash"] if last_block else "0"
                
                # 1. Generate Fake Signed Transactions
                fake_transactions = []
                for i in range(num_transactions):
                    payload = {
                        "person_name": f"Hacker {i+1}",
                        "person_email": f"hacker{i+1}@darknet.xyz",
                        "course": "Advanced Blockchain Exploitation",
                        "certification_date": str(datetime.now().date()),
                        "institution": "Dark Web Academy",
                    }
                    signed_tx = sign_transaction(payload, private_key)
                    if signed_tx:
                        fake_transactions.append(signed_tx)
                
                if len(fake_transactions) > 0:
                    # 2. Mine the block on the UI
                    with st.spinner(f"Mining Attack Block (Index: {index}) on UI..."):
                        nonce = 0
                        import hashlib
                        difficulty = 4  # System difficulty (from config)
                        
                        while True:
                            timestamp_str = str(datetime.now())
                            data = json.dumps(
                                {
                                    "index": index,
                                    "timestamp": timestamp_str,
                                    "transactions": fake_transactions,
                                    "previous_hash": previous_hash,
                                    "nonce": nonce,
                                },
                                sort_keys=True,
                                default=str,
                            )
                            hash_val = hashlib.sha256(data.encode()).hexdigest()
                            if hash_val.startswith("0" * difficulty):
                                break
                            nonce += 1
                            
                        attack_block = {
                            "index": index,
                            "timestamp": timestamp_str,
                            "transactions": fake_transactions,
                            "previous_hash": previous_hash,
                            "nonce": nonce,
                            "hash": hash_val
                        }
                    
                    st.success(f"Block Successfully Mined! Nonce: {nonce}, Hash: {hash_val}")
                    with st.expander("View Mined Attack Block", expanded=False):
                        st.json(attack_block)
                    
                    # 3. Post to Node
                    with st.spinner(f"Injecting Block to {target_node_block}..."):
                        try:
                            response = requests.post(f"{node_url}/blocks", json=attack_block, timeout=5)
                            response.raise_for_status()
                            st.success("Attack successful! Block posted and accepted by the node.")
                            st.json(response.json())
                            st.balloons()
                        except Exception as e:
                            st.error(f"Error posting attack block: {e}")
                            if hasattr(e, "response") and e.response is not None:
                                try:
                                    st.error(f"Server response: {e.response.json()}")
                                except Exception:
                                    st.error(f"Server response text: {e.response.text}")
