import streamlit as st
import httpx, asyncio 


API_ENDPOINT = "http://python-gpt-app:3000/"
TIMEOUT = 60
async def send_api_request(input_data):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        
        response = await client.post(API_ENDPOINT + "query_chatgpt",
                                     json={'code': input_data})
    if response.status_code == 200:
        response_json = response.json()
        return response_json

async def upload_file(file):
    # Handle the uploaded file, for example, unzip it:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(API_ENDPOINT + "create_nodes_store", files={'file': file})
    if response.status_code == 200:
        files_updated = response.json()['py_files']
        return files_updated
    
async def update_nodes_store():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(API_ENDPOINT + "update_nodes_store")
    if response.status_code == 200:
        files_updated = response.json()['py_files']
        return files_updated

        
async def main():
    st.title("CHATGPT for your Python repository")
    
    placeholder = st.empty()
    if st.sidebar.button("Update your database", key="additional_api_call"):
        with st.spinner("Updating database..."):
            response = await update_nodes_store()
            st.success("Updated successful")
            placeholder.write("Additional Information:")
            st.json(response)  # Displaying additional information
            await asyncio.sleep(5)  # Display response for 10 seconds
            placeholder.empty()  # Clear the output after 10 seconds

    input_data = st.text_area("Input Data:", key="chatgpt_answer")
    if st.button("Submit"):
        with st.spinner("Loading message..."):
            response = await send_api_request(input_data)
            answer, file, parent, relations, nodes = response['answer'], response['file_of_context'], response['parent_of_context'], response['most_similar_relations'], response['nodes']
            short_text_relations = {}
            max_n_words = 250
            for relation_id, text in relations.items():
                short_text_relations[relation_id] = " ".join([word for word in text.split(" ")[:max_n_words]])
            st.success(answer)
            st.json({'file': file, 'parent_node': parent, 'relations': short_text_relations, 'nodes': nodes})
    st.write("---")

    uploaded_file = st.file_uploader("Upload .zip File", key="upload_zip_file")
    if uploaded_file is not None:
        with st.spinner("Uploading..."):
            files_updated = await upload_file(uploaded_file)
            st.success("File uploaded successfully")
            st.json({'files': files_updated})
        uploaded_file = None
            
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
