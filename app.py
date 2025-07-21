import streamlit as st
import arxiv
import torch
import gc
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Configs
NUM_PAPERS = 2
LLM_MODEL = "MBZUAI/LaMini-Flan-T5-248M"

# Load model with caching to reduce memory use
@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(LLM_MODEL)
    return tokenizer, model

tokenizer, model = load_model()

# Prompt template
def build_prompt(summaries):
    return f'''
Write a structured academic literature review (around 1200 words) based on the following summaries.

Summaries:
{summaries}

Include these sections:
1. Introduction
2. Key Approaches and Findings
3. Comparative Analysis
4. Gaps and Future Directions

Finish with a properly formatted bibliography using inline metadata.
Use formal academic language.
'''

# Get paper summaries from arXiv
def fetch_papers(topic):
    search = arxiv.Search(query=topic, max_results=NUM_PAPERS, sort_by=arxiv.SortCriterion.Relevance)
    results = list(search.results())
    summaries = []
    bib_entries = []

    for i, result in enumerate(results):
        abstract = result.summary.replace("\n", " ").strip()
        meta = f"{result.authors[0].name} et al. ({result.published.year}). *{result.title}*. arXiv. {result.entry_id}"
        summaries.append(f"- {abstract}")
        bib_entries.append(f"{i+1}. {meta}")

    return "\n".join(summaries), "\n".join(bib_entries)

# Generate literature review
def generate_review(topic):
    summaries, bibliography = fetch_papers(topic)
    prompt = build_prompt(summaries)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
    output = model.generate(**inputs, max_new_tokens=600)
    review = tokenizer.decode(output[0], skip_special_tokens=True)

    # Cleanup memory
    torch.cuda.empty_cache()
    gc.collect()

    return review, bibliography

# Streamlit UI
st.title("🧠 AI Researcher: Literature Review Generator")
st.write("Enter a research topic to generate a structured literature review based on arXiv papers.")

topic = st.text_input("Enter research topic", value="Medical AI")

if st.button("Generate Review"):
    with st.spinner("Fetching papers and generating review..."):
        review, bibliography = generate_review(topic)
        st.subheader("📘 Literature Review")
        st.write(review)
        st.subheader("📚 Bibliography")
        st.markdown(bibliography)