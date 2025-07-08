# pip install ollama
# install ollama: https://ollama.com/download
# ollama pull llama3.2-vision:11b
# ollama pull minicpm-v
# check if gpu being used: ollama ps
# make sure ollama is running
import ollama
from PIL import Image
import os
import subprocess
import time
import requests

def load_image_bytes(image_path):
	#print(f"Loading image from local path: {image_path}")
	with open(image_path, "rb") as f:
		return f.read()

def run_llama_vision_ollama(prompt, image_path_or_url):
	model_name = 'minicpm-v' #'llama3.2-vision:11b'
	try:
		image_bytes = load_image_bytes(image_path_or_url)
		#print(f"\nSending prompt ({model_name}): '{prompt}'")
		response = ollama.chat(
			model=model_name,
			options={'keep_alive': 0},
			messages=[
				{
					'role': 'user',
					'content': prompt,
					'images': [image_bytes],
				}
			]
		)
		# The output format from Ollama is typically a dictionary containing 'message' with 'content'
		return response['message']['content']
	except Exception as e:
		print(f"Error during Ollama inference: {e}")
		return None
	
def get_tags_from_image(image_path, tag_list):
	tags = []
	for t in tag_list:
		prompt = f"Does this image contains, depict or is applicable to the tag [{t}]? 'Yes' or 'No'"
	
		output_json = run_llama_vision_ollama(
			prompt=prompt,
			image_path_or_url=image_path
		)

		if output_json[0] == "Y":
			tags.append(t)

	return ", ".join(tags)

# if __name__ == "__main__":
# 	try:
# 		Image.new('RGB', (60, 30), color = 'red').save('example_image.jpg')
# 	except Exception as e:
# 		print(f"Could not create dummy image: {e}. Please ensure you have Pillow installed (pip install Pillow).")

# 	local_image_path = "example_image.jpg"
# 	if not os.path.exists(local_image_path):
# 		print(f"Warning: {local_image_path} not found. Please provide a valid local image path or create one.")
# 	else:
# 		print("--- Example 1: Describing a Local Image ---")
# 		output_local = run_llama_vision_ollama(
# 			prompt="Describe this image in detail.",
# 			image_path_or_url=local_image_path
# 		)
# 		print("Model Output (Local Image):", output_local)

# 	# Example with a specific output format request
# 	print("\n--- Example 3: Requesting a specific output format ---")
# 	output_format_prompt = """Describe the main object in this image.
# 	Provide the output in a JSON format with the following keys:
# 	{
# 	  "object_type": "string",
# 	  "main_color": "string",
# 	  "description": "string"
# 	}
# 	"""
# 	output_json = run_llama_vision_ollama(
# 		prompt=output_format_prompt,
# 		image_path_or_url=local_image_path # Or any image you prefer
# 	)
# 	print("Model Output (JSON format request):", output_json)