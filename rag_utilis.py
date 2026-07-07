from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vector_store = FAISS.load_local(
    "faiss_index",
    embedding_model,
    allow_dangerous_deserialization=True
)

"""
def retrieve_solution(disease_name):
    results = vector_store.similarity_search(disease_name, k=2)
    return results[0].page_content
"""  

def retrieve_solution(disease_name):

    results = vector_store.similarity_search(disease_name, k=1)
    if len(results)==0:
        return None
    text = results[0].page_content
    #text = "\n".join([doc.page_content for doc in results])

    data = {
        "summary": "",
        "symptoms": [],
        "immediate_action": [],
        "prevention": [],
        "treatment": [],
        "fungicides": []
    }

    current_section = None

    for line in text.split("\n"):

        line = line.strip()

        if not line:
            continue

        if line.startswith("Disease:"):
            data["summary"] = line.replace("Disease:", "").strip()

        elif line.startswith("Symptoms:"):
            current_section = "symptoms"

        elif line.startswith("Immediate Action:"):
            current_section = "immediate_action"

        elif line.startswith("Prevention:"):
            current_section = "prevention"

        elif line.startswith("Treatment:"):
            current_section = "treatment"

        elif line.startswith("Recommended Fungicides:"):
            current_section = "fungicides"

        elif line.startswith("-"):

            if current_section:
                data[current_section].append(
                    line.replace("-", "").strip()
                )

    return data