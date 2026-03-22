#%%
import os

current_dir = r"C:\my\codes\gallery_web"
print(current_dir)
COMMENTS_DIRECTORY = os.path.join(current_dir, 'comments')
AUDIO_DIRECTORY = os.path.join(current_dir, 'audio')
TEMP_DIRECTORY = os.path.join(current_dir, 'temp')

for folder in [COMMENTS_DIRECTORY,AUDIO_DIRECTORY,TEMP_DIRECTORY]:
    if os.path.isdir(folder):
        for file_name in os.listdir(folder):
            file_path=os.path.join(folder,file_name)
            print('deleting ',file_path)
            os.remove(file_path)

# %%
