# Data Engineering Individual Project - Recipe Aggregation

This is the GitHub repository for MSIN0166 Data Engineering

This project aims to take recipes, ingredients and nutritional values from across the web, compile and augment the data ready for machine learning.

Potential applications include meal planning suggestion or nutrition value prediction.

This project was designed so that any implementation can run on Google Cloud Platform. Cloud functions code can be found in GCP folder, however please remember it is necessary to add API keys etc.

```pip install requirements.txt``` to install prerequisites.

All the folders named ```Edamam, TheMealDB, TastyAPI and SimplyRecipes``` contain the notebooks and scripts that were used to extract data from these sources. However these scripts have then been compiled within the Cloud Functions and that is the code that is live. You can find the cloud functions in the ```GCP-Operations``` folder.

To set up this pipeline you should set up two Cloud Storage Buckets, one MySQL database and one Neo4j database. You can see where to add this in the Cloud Functions code.
