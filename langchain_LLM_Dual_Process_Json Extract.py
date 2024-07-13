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
import re
import json

def json_str_to_dict(json_str):
    return json.loads(json_str)

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
#query = "show me the installation procedure of the O2O teaching system?"
#query = "show me the Three-point Mode callibration?"
#query = "what is Teleoperation in O2O system?"
#query = "Direct Entry?"
#query = "make the robot move second cup to third position and first cup to second position?"

query = "make the robot move second cup to third position and first cup to second position?"
#query = "make the robot move all cup in second place?"
query = "make the robot move all cup in in the next position and the last in first position?"
#query = "向我展示 O2O 中的安川運動錄音嗎？"
result = docsearch.similarity_search(query)
#print(result[0])

rag_custom_prompt = PromptTemplate.from_template(bot_sys_template)

# Set up the RAG chain
response_a = llm.chat.completions.create(
    model=AZURE_OPENAI_DEPLOYMENT_NAME_CHAT , # model = "deployment_name".
    temperature=0.9,
    messages=[
        {"role": "system", "content": """I have three cup, first is in the left and the third is in the right. Then I have a robot that have skill to go initial position, pick a cup, place a cup, and retract\n
               Then you also know that\n\n"""+ str(result[0])},
        {"role": "user", "content": "move the cup two and three in the fist place"},
        {"role": "assistant", "content": """json_for_answer_user= {"message": "Sure! I will make the robot move."}\nlist steps_command_robot= [Pick Cup Two, Put Cup in fist place, Pick Cup Three, Put Cup in fist place, Retract]"""},   

        {"role": "user", "content": query+" Write the step based on the robot skill and add all on the list steps_command_robot:[...]}"}
    ]
)

print(response_a.choices[0].message.content)

pattern = r'steps_command_robot=\s*\[(.*?)\]'
matches = re.search(pattern, response_a.choices[0].message.content, re.DOTALL)
print("######################################################")
print("\nMathch:")
commands_robot=""
cmds_temp= [] 
cmd_temp = {"command": "-", "argument_1": "-", "argument_2": "-", "argument_3": "-"}
cmd_to_robot={"robot_type": "j2n6s300","robot_id": 0,"commands":""}

if matches:
    # Extract the matched content
    commands_robot_str = matches.group(1)
    
    # Convert the string representation of list to actual Python list
    commands_robot = commands_robot_str.split(', ')
    
    # Print or use the commands_robot list as needed
    for i in range(len(commands_robot)):
        print(commands_robot[i])
else:
    print("List not found in the input string.")
print("\n")
for i in range(len(commands_robot)):
    response_b = llm.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT_NAME_CHAT , # model = "deployment_name".
        temperature=0.95,
        messages=[
            {"role": "system", "content": """You are hucenrotia-assistant, you will always give result only single json separately, one for user and the other for give command to robot. 
                   Use this json template to control the robot\n
                   json_command_robot = {\n"robot_type": robot_type_value,\n "robot_id": robot_id_value,\n "command": command,\n "argument_1": argument_1,\n "argument_2": argument_2,\n "argument_3": argument_3}\n
                   The robot type is j2n6s300 and robot id is 0\n
                   Let we have total 3 cup, the most left has id 1 and most right has id 3. The ball is under cup 2. First position is most left position and third position is thelast position.\n
                   Use this rule\ncommand=0 for make robot go to initial position or homing, param1 to 3=-\ncommand=1 for make robot go to cup the grab the cup or show inside the cup or lift the cup, param1=type(int) is target cup id, param 2 to 3=-\ncommand=2 for make robot go to then put the cup, param1=type(int) is target cup id, param 2 to 3=-, command=3 for make robot retract on the above of cup, param1=type(int) is target cup id, param 2 to 3=-\n target cup is position that ask by question\n for return or put back choose same position as target cup that was choosen\n"""},
            {"role": "user", "content": "Pick Cup Two"},
            {"role": "assistant", "content": """json_command_robot= {"robot_type": "j2n6s300",\n"robot_id": "0",\n"command": "1",\n"argument_1": "2",\n"argument_2": "-",\n"argument_3": "-"}"""},   

            {"role": "user", "content": commands_robot[i]+", only answer using single json tempate\n json_command_robot={...}"}
        ]
    )
    #Get json result
    # Regular expressions to extract JSON strings
    json_robot_pattern = re.compile(r'json_command_robot\s*=\s*({.*?})', re.DOTALL)

    # Extract JSON strings
    json_robot_match = json_robot_pattern.search(response_b.choices[0].message.content)
    if json_robot_match:
        _json_command_robot = json.loads(json_robot_match.group(1))
        cmd_temp["command"] = _json_command_robot.get('command', "")
        cmd_temp["argument_1"]  = _json_command_robot.get('argument_1', "")
        cmd_temp["argument_2"]  = _json_command_robot.get('argument_2', "")
        cmd_temp["argument_3"]  = _json_command_robot.get('argument_3', "")

    # Print the result
    print(cmd_temp)
    json_cmd_temp = json.dumps(cmd_temp)
    #print(json_cmd_temp)
    cmds_temp.append(json_cmd_temp)
    #print(cmds_temp)
    #print(response_b.choices[0].message.content+"\n")
print("######################################################")
# Print the list of dictionaries
print(cmds_temp)
print(len(cmds_temp))
print("######################################################")
# Convert each JSON-like string to dictionary
dict_cmds_temp = [json_str_to_dict(json_str) for json_str in cmds_temp]
print(dict_cmds_temp)
print("######################################################")
cmd_to_robot["commands"] = dict_cmds_temp
print(cmd_to_robot)
print("######################################################")
json_cmd_to_robot = json.dumps(cmd_to_robot)
print(json_cmd_to_robot)
