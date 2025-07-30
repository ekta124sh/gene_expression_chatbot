import streamlit as st
import mysql.connector
import re
import pandas as pd

# Custom theme styles using HTML
st.markdown("""
    <style>
        body {
            background-color: #C4C3D0;
            color: #fafafa;
        }
        .block-container {
            padding: 2rem 2rem;
            background-color: #1e222e;
            border-radius: 12px;
        }
        .stChatMessage {
            padding: 1rem;
            border-radius: 16px;
            margin-bottom: 1rem;
        }
        .stChatMessage.user {
            background-color: #2c3e50;
            color: white;
        }
        .stChatMessage.assistant {
            background-color: #34495e;
            color: white;
        }
        table {
            background-color: white;
            color: black;
        }
    </style>
""", unsafe_allow_html=True)

# Page title
st.markdown("<h1 style='text-align:center; color:#5dade2;'>🧬 Gene Expression Assistant</h1>", unsafe_allow_html=True)

# Function to get gene expression data from gexpression table
def get_gene_expression(gene=None, tissue=None, condition=None):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",
        database="GeneExpressionDB"
    )
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM gexpression WHERE 1=1"
    params = []

    if gene:
        query += " AND g_name LIKE %s"
        params.append(f"%{gene}%")
    if tissue:
        query += " AND tissue LIKE %s"
        params.append(f"%{tissue}%")
    if condition:
        query += " AND condition_a LIKE %s"
        params.append(f"%{condition}%")

    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Ask about gene expression (e.g., 'lung tissue for gene BRCA1')")

# If user sends a message
if user_input:
    st.chat_message("user").markdown(f"💬 *You:* {user_input}")
    st.session_state.messages.append({"role": "user", "content": f"💬 *You:* {user_input}"})

    # Improved parsing using regex
    gene = tissue = condition = None
    text = user_input.lower()

    # Extract gene
    gene_match = re.search(r"gene\s+([a-zA-Z0-9_-]+)", text)
    if gene_match:
        gene = gene_match.group(1)

    # Extract tissue
    tissues_list = ["lung", "brain", "heart", "liver", "kidney", "skin"]
    for t in tissues_list:
        if t in text:
            tissue = t
            break

    # Extract condition
    condition_match = re.search(r"condition\s+([a-zA-Z0-9_-]+)", text)
    if condition_match:
        condition = condition_match.group(1)

    # Fetch results
    result = get_gene_expression(gene=gene, tissue=tissue, condition=condition)

    # Build assistant response
    assistant_response = "🤖 *Assistant Response:*\n\n"

    if gene or tissue or condition:
        assistant_response += "🔎 *Search Parameters:*\n"
        if gene: assistant_response += f"• Gene: `{gene}`\n"
        if tissue: assistant_response += f"• Tissue: `{tissue}`\n"
        if condition: assistant_response += f"• Condition: `{condition}`\n"
        assistant_response += "\n"
    else:
        assistant_response += "⚠️ I couldn’t detect any gene, tissue, or condition in your message. Try again using keywords like `gene`, `lung`, or `condition infected`.\n\n"

    if result:
        assistant_response += f"✅ *Found {len(result)} result(s):*"
        st.chat_message("assistant").markdown(assistant_response)
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

        # Show results as a table
        df = pd.DataFrame(result)
        st.dataframe(df)
    else:
        assistant_response += "❌ No matching records found."
        st.chat_messa_
