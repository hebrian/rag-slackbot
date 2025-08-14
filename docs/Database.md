# Databases
> For my project, I incorporated 2 main databases. In the future I would incorporate additional ones depending on the needs of the organization.

I have provided two dummy versions of the databases so viewers can see how the agent interacts with them. You may replace each database as needed, but make sure you also update the tools for the agent and the agent prompt as well. 

## Vector Database (Unstructured Data)
ChromaDB was used as the lightweight vector database to store unstructured text data from documents retrieved from the organization's google drive. The chroma_db folder provided is an example database of 4 google documents being decomposed into 27 chunks and stored as embeddings. The text data for these 4 documents are scrapped from CYI's public facing website for each of it's major programs in order to allow someone using this repo to get a sense of how it works. In the actual solution I connected to private unstructured text data (ie. google documents) in the organization's google drive to create the vector database. 

## SQLite (Strucutred Data)
Since the organization also had structured data in the form of google sheets, I have an included a dummy version of the SQLite database I used named **cyi_directory.db**. This database is composed of 10 rows with dummy names and contact information to show how the agent can use text-to-sql tools to answer questions given by a user.


