import cohere
from dotenv import load_dotenv
import os

# Load environment variables (Cohere API Key)
#load_dotenv()
#COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# instantiate the Cohere client
co = cohere.ClientV2("H6zrNmbl9Rf4k7Z0TjdHrgjD2rCwHJLGOtj939WR")


# single-label dataset
single_label_dataset = co.datasets.create(
    name="single-label-dataset",
    data=open(r"C:\Users\baliq\Desktop\Review_Analysis\sentiment_data.jsonl", "rb"),
    type="single-label-classification-finetune-input",
)

print(co.wait(single_label_dataset))

# create dataset
single_label_dataset = co.datasets.create(
    name="single-label-dataset",
    data=open(r"C:\Users\baliq\Desktop\Review_Analysis\sentiment_data.jsonl", "rb"),
    type="single-label-classification-finetune-input",
)

print(co.wait(single_label_dataset).dataset.validation_status)

# start the fine-tune job using this dataset
from cohere.finetuning.finetuning import (
    BaseModel,
    FinetunedModel,
    Settings,
)

single_label_finetune = co.finetuning.create_finetuned_model(
    request=FinetunedModel(
        name="single-label-finetune",
        settings=Settings(
            base_model=BaseModel(
                base_type="BASE_TYPE_CLASSIFICATION",
            ),
            dataset_id=single_label_dataset.id,
        ),
    ),
)

print(
    f"fine-tune ID: {single_label_finetune.finetuned_model.id}, fine-tune status: {single_label_finetune.finetuned_model.status}"
)
