from PyPDF2 import PdfReader
from langchain_community.document_loaders import PyPDFLoader

from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import ElasticVectorSearch, Pinecone, Weaviate, FAISS
import os
from langchain.chains.question_answering import load_qa_chain
#from langchain.llms import OpenAI
from langchain_openai import AzureOpenAI,AzureOpenAIEmbeddings,OpenAIEmbeddings
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, ChainedTokenCredential, ManagedIdentityCredential, AzureCliCredential
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

save_res=False

### Get your API keys from openai, you will need to create an account. 
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_DEPLOYMENT_NAME_CHAT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_CHAT")

credential = DefaultAzureCredential()

llm = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=OPENAI_API_VERSION,
)
### embeding
embeddings = AzureOpenAIEmbeddings(
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
    openai_api_version=OPENAI_API_VERSION,#"2023-05-15",
)
#embeddings = OpenAIEmbeddings()
### location of the pdf file/files. 
if(save_res):
    reader=PdfReader('O2O_manual.pdf')
    '''
    loader = PyPDFLoader("O2O_manual.pdf", extract_images=True)
    docs = loader.load_and_split()
    '''
    ###PdfReader
    ### read data from the file and put them into a variable called raw_text then split on smaller     chunks so that during information retreival we don't hit the token size limits. 
    raw_text = ''
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            raw_text += text


    text_splitter = CharacterTextSplitter(        
        separator = "\n",
        chunk_size = 1500,
        chunk_overlap  = 400,
        length_function = len,
    )
    texts = text_splitter.split_text(raw_text)
    

    #print(type(texts[4]))
    #print(texts[4])

    ### embeding process

    docsearch = FAISS.from_texts(texts, embeddings)
    #docsearch = FAISS.from_documents(docs, embeddings)
    docsearch.save_local("faiss_index")
else:
    docsearch = FAISS.load_local("faiss_index", embeddings,allow_dangerous_deserialization=True)

#print(docsearch.index.ntotal)

bot_sys_template = "You are Hucenrotia-Assistant.\nAnswer the this question: {question}"
#query = "show me the O2O Software Interface Operation?"
#query = "show me the Offline Trajectory Recording of O2O Software Interface Operation?"
#query = "show me the YASKAWA Motion Recordingg in O2O?"
#query = "what is YRC1000 controller?"
query = "show me the installation procedure of the O2O teaching system?"
#query = "show me the Three-point Mode callibration?"
#query = "what is Teleoperation in O2O system?"
#query = "Direct Entry?"
#query = "向我展示 O2O 中的安川運動錄音嗎？"
result = docsearch.similarity_search(query)
#print(result[0])

rag_custom_prompt = PromptTemplate.from_template(bot_sys_template)

# Set up the RAG chain
response = llm.chat.completions.create(
    model=AZURE_OPENAI_DEPLOYMENT_NAME_CHAT , # model = "deployment_name".
    temperature=0.95,
    messages=[
        {"role": "system", "content": str(result[0])},
        {"role": "user", "content": query}
    ]
)

print(response.choices[0].message.content)

# Print the result

#print(answer)
