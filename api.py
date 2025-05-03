import fastapi
from fastapi import FastAPI, File, Form,UploadFile
from fastapi.responses import FileResponse
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama,OllamaLLM,OllamaEmbeddings
from fastapi.responses import JSONResponse
import speech_recognition as sr
from typing import Optional
from langchain.schema import SystemMessage, HumanMessage, AIMessage


app=FastAPI()



@app.post("/Speech_input_file")
async def speech_parsing_file(
    file: Optional[UploadFile] = File(default=None),
    prompt: Optional[str] = Form(default=None)
):
    system_prompt="You are a cloud assistant. Given the user command, identify the intent (create VM, delete volume, resize VM, etc.) and extract key details like resource name,size,flavor. Give Precise answers and in Markdown format. Give answers in a table format when needed"
    # system_prompt+="""Give in JsonFormat as a json file no Markdown at the end of the Response stating :
    # {"Resource Type":	{},

    # "Flavor":{}
    # "Name":{}
    # }"""
    operation_list=['VM Provisioning','VM Resizing','VM Deletion','Network Creation','Volume Operations','Usage Query']
    system_promp2="""“You are a cloud assistant. Given the user command, identify the intent (create VM, delete volume, resize VM, etc.) and extract key details like resource name,size,flavor.” Give output only as in JsonFormat as a json file Response stating :
    json_response:
    
    {"Resource Type":	{},(must include)
    "Operation": one from the ['Create VM','Resize','Deletion','Network Creation','Volume Create','Delete Volume','Usage Query'], (must include)
    if usage querry provided -> "querry": conatining usage querry,

    "Flavor":{},(must include)
    "Name":{},(must include)
    "network":{}(must include)
    "image":{}(must include)
    "size":{}(must include should always be in lowercase and in integer format)
    }

    Generate a JSON response in a single continuous line without including escape characters such as '\', newline ('\n'), or tab ('\t'). Ensure proper formatting and readability
    """
    text = ""
    media = None

    if file:
        try:
            # Save the uploaded file temporarily for speech recognition
            with open("temp_audio.wav", "wb") as buffer:
                buffer.write(await file.read())

            recognizer = sr.Recognizer()
            with sr.AudioFile("temp_audio.wav") as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
            
            media = "audio/mpeg"

            if prompt:
                text += "\n" + prompt
                media = ["audio/mpeg", "text"]
        except Exception as e:
            return JSONResponse(content={"error": f"Audio processing failed: {str(e)}"}, status_code=400)

    elif prompt:
        text = prompt
        media = "text"
    else:
        return JSONResponse(content={"error": "Neither file nor prompt was provided."}, status_code=400)

    try:
        model_name = "llama3.2:latest"
        llm = OllamaLLM(model=model_name)
        messages=[SystemMessage(content=system_prompt),HumanMessage(content=prompt)]
        
        response = llm.invoke(messages)

        messages2=[SystemMessage(content=system_promp2),HumanMessage(content=prompt)]
        json_output=llm.invoke(messages2)
        cleaned_string = json_output.replace("\\", "")
        cleaned_strings=cleaned_string.replace("\n", "")

        print(cleaned_strings)

        responses = {
            "response": response,
            "media_type": media,
            "file_name": file.filename if file else None,
            "file_text": text,
            "json_outputs":cleaned_strings

        }
        print(responses)
        return JSONResponse(content=responses)
    except Exception as e:
        return JSONResponse(content={"error": f"LLM invocation failed: {str(e)}"}, status_code=500)
