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

def check_transaction(url: str, tx_id: str):
    try:
        response = requests.get(f"{url}/transactions/{tx_id}", timeout=3)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
    except Exception:
        return {"error": "Connection failed"}


def sign_transaction(payload: dict, private_key_hex: str, force_id: str | None = None, force_timestamp: str | None = None) -> dict | None:
    tx_id = force_id or str(uuid.uuid4())
    timestamp_str = force_timestamp or str(datetime.now())

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

tab1, tab_verify, tab2, tab3, tab4 = st.tabs(["📊 Ledger Visualization", "🔍 Verify Certificate", "Send Transaction", "🛠️ Simulate Attack", "🎲 Random TXs"])

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

# --- TAB: VERIFY CERTIFICATE ---
with tab_verify:
    st.header("Verify Certificate")
    st.markdown("Enter a Certificate Transaction Hash/ID to check its validity and status in the blockchain.")
    
    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        verify_node = st.selectbox("Select Node to Query", list(NODES.keys()), key="verify_target_node")
        tx_hash_input = st.text_input("Transaction Hash / ID", placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000")
        
    if st.button("Verify Certificate 🔍", use_container_width=True):
        if not tx_hash_input:
            st.error("Please enter a Transaction Hash to verify.")
        else:
            node_url = NODES[verify_node]
            with st.spinner("Querying blockchain..."):
                result = check_transaction(node_url, tx_hash_input.strip())
                
            if result is None:
                st.error("❌ Certificate NOT FOUND in this node's mempool or blockchain.")
            elif "error" in result:
                st.error("⚠️ Failed to connect to the node.")
            else:
                if result["status"] == "confirmed":
                    st.success(f"✅ Certificate FOUND and CONFIRMED in Block {result['block_index']}!")
                else:
                    st.info("🕒 Certificate found in MEMPOOL (Waiting to be mined...)")
                
                with st.expander("Certificate Details", expanded=True):
                    st.json(result["transaction"])

# --- TAB 3: SIMULATE ATTACK ---
with tab3:
    st.header("Simulate Attack (Direct Block Injection)")
    st.markdown("Create a valid block with random transactions to test if the node accepts it. The UI acts as a malicious miner, signs fake transactions, calculates the Proof of Work, and injects the block directly.")
    
    col_target, col_empty = st.columns([1, 1])
    with col_target:
        target_node_block = st.selectbox("Select Target Node for Attack", list(NODES.keys()), key="simulate_attack_target")
        private_key = st.text_input("Attacker Private Key (Hex)", type="password", help="Required to sign the injected fake transactions")
        num_transactions = st.number_input("Number of Fake TXs", min_value=1, max_value=10, value=2)
        force_accept = st.checkbox("Force Accept (Bypass Signature Validation)", value=False, help="Injects the force_accept=True flag into the block telling the node to ignore fake signatures.")
    
    if st.button("Generate, Mine & Inject Block 💥", use_container_width=True):
        if not private_key and not force_accept:
            st.error("Private Key is required to sign the fake transactions! (Unless you check Force Accept)")
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
                            "hash": hash_val,
                            "force_accept": force_accept
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

# --- TAB 4: RANDOM TXs ---
with tab4:
    st.header("Send Random Transactions")
    st.markdown("Generate and send a batch of random (but deterministic via SEED) transactions to a specific node.")
    
    col_target_random, col_empty_random = st.columns([1, 1])
    with col_target_random:
        target_node_random = st.selectbox("Select Target Node", list(NODES.keys()), key="random_tx_target")
        private_key_random = st.text_input("Private Key (Hex)", type="password", key="random_tx_pk", help="Required to sign the transactions")
        num_txs = st.number_input("Number of Transactions", min_value=1, max_value=50, value=5)
        seed_value = st.number_input("Random SEED", value=42, help="Used for deterministic randomness. The same seed produces the exact same transactions!")
    
    if st.button("Generate & Send Transactions 🚀", use_container_width=True):
        if not private_key_random:
            st.error("Private Key is required to sign the transactions!")
        else:
            import random
            
            # Use seed to guarantee reproducibility
            random.seed(seed_value)
            
            courses = ["Sistemas Distribuídos", "Redes de Computadores", "Engenharia de Software", "Banco de Dados", "Inteligência Artificial"]
            institutions = ["UFRN", "USP", "UNICAMP", "UFC", "UFPE"]
            domains = ["gmail.com", "ufrn.edu.br", "hotmail.com", "yahoo.com"]
            
            node_url = NODES[target_node_random]
            success_count = 0
            
            with st.spinner(f"Generating and sending {num_txs} transactions..."):
                for i in range(num_txs):
                    # Generate deterministic random data based on seed
                    random_id = random.randint(1000, 9999)
                    
                    payload = {
                        "person_name": f"Student {random_id}",
                        "person_email": f"student{random_id}@{random.choice(domains)}",
                        "course": random.choice(courses),
                        "certification_date": f"2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                        "institution": random.choice(institutions),
                    }
                    
                    # Make ID and timestamp deterministic based on the seed sequence
                    det_id = str(uuid.UUID(int=random.getrandbits(128), version=4))
                    det_ts = f"2026-04-08 12:00:{random.randint(0,59):02d}.123456"
                    
                    tx_dict = sign_transaction(payload, private_key_random, force_id=det_id, force_timestamp=det_ts)
                    if tx_dict:
                        result = send_transaction(node_url, tx_dict)
                        if result:
                            success_count += 1
            
            if success_count == num_txs:
                st.success(f"Successfully sent all {success_count} transactions to {target_node_random}!")
                st.balloons()
            elif success_count > 0:
                st.warning(f"Sent {success_count}/{num_txs} transactions successfully.")
            else:
                st.error("Failed to send transactions.")
            
            # Reset seed to avoid affecting other parts of the script
            random.seed()

