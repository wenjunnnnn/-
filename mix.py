from dotenv import load_dotenv
import os

################################################### 讀入文章，翻譯文章。 ###################################################################

from azure.ai.translation.text import *
from azure.ai.translation.text.models import InputTextItem

translatorRegion = "globals"
translator_key = "86d976947b6444dda2d079c987265da8"

# Create client using endpoint and key
credential = TranslatorCredential(translator_key, translatorRegion)
client = TextTranslationClient(credential)

## Choose target language
languagesResponse = client.get_languages(scope="translation")

targetLanguage = "en"
supportedLanguage = False
while supportedLanguage == False:
    if targetLanguage in languagesResponse.translation.keys():
        supportedLanguage = True
    else:
        print("{} is not a supported language.".format(targetLanguage))

# Translate text

org_file = "article2.txt"        

if not os.path.exists(org_file):
    print(org_file + "文件不存在")
    exit()

inputText = ""
with open(org_file, 'r', encoding="utf-8") as file:
    inputText = file.read()
input_text_elements = [InputTextItem(text=inputText)]
translationResponse = client.translate(content=input_text_elements, to=[targetLanguage])
translation = translationResponse[0] if translationResponse else None
if translation:
    sourceLanguage = translation.detected_language

with open("org_translated.txt", "w", encoding="utf-8") as translate_file:
    for translated_text in translation.translations:
        translate_file.write(translated_text.text)

################################################### 讀入文章，並進行文本分析，提取關鍵字。 ###################################################

# Import namespaces
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

def Analysis(org_file_name="org_translated.txt", translated="org_translated.txt", sourceLan="English"):
    try:
        # Get Configuration Settings
        load_dotenv()
        ai_endpoint = "https://group2-lan.cognitiveservices.azure.com/"
        ai_key = "b6267d98f5f54328a160d6054a64f557"

        # Create client using endpoint and key
        credential = AzureKeyCredential(ai_key)
        cog_client = TextAnalyticsClient(endpoint=ai_endpoint, credential=credential)


        # Read the file contents
        print('\n-------------' + org_file_name + '-------------' )
        text_org = open(os.path.join(org_file_name), encoding='utf8').read()
        text = open(os.path.join(translated), encoding='utf8').read()
        #print('\n' + text)
            
        # Get language 檢測語言
        detectedLanguage = cog_client.detect_language(documents=[text_org])[0]
        print('\nLanguage: {}\n'.format(detectedLanguage.primary_language.name))

        # Get key phrases and save to keyword.txt
        phrases = cog_client.extract_key_phrases(documents=[text])[0].key_phrases

        # 建立一個字典來存儲每個關鍵字的出現位置 
        phrase_positions = {}
        for phrase in phrases:
            position = text.find(phrase)
            if position != -1:
                phrase_positions[phrase] = position

        # 按出現位置排序關鍵字
        sorted_phrases = sorted(phrases, key=lambda phrase: phrase_positions[phrase])

        with open('keyword.txt', 'w') as file:  # 'a' 模式代表追加到文件末尾
            #print("\nSorted Key Phrases:")
            for phrase in sorted_phrases:
                #print('\t{}'.format(phrase))
                file.write(phrase + '\n')  # 将关键词写入文件并换行

    except Exception as ex:
        print(ex)

Analysis(org_file_name=org_file, sourceLan=sourceLanguage.language)



########################################################## 將關鍵字轉為文本摘要。 ##########################################################


from transformers import pipeline
import os

if not os.path.exists("keyword.txt"):
    print("keyword.txt文件不存在")
    exit()


# 讀取關鍵字
with open("keyword.txt", "r") as file:
    keywords = file.read().splitlines()

# 将关键词转换为一段文本
keywords_text = ", ".join(keywords)

# 加载一个预训练的摘要生成模型，这里使用BART模型
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# 生成摘要
summary = summarizer(keywords_text, max_length=300, min_length=80, do_sample=False)

# 打印摘要
# print(summary[0]['summary_text'])

# 将摘要写入 abstract.txt 文件
with open("abstract.txt", "w", encoding="utf-8") as abstract_file:
    abstract_file.write(summary[0]['summary_text'])

print("文本摘要已寫入 abstract.txt 文件。\n")


############################################## 將摘要語言翻譯為繁體中文。 ###################################################################

# Create client using endpoint and key
credential = TranslatorCredential(translator_key, translatorRegion)
client = TextTranslationClient(credential)

## Choose target language
languagesResponse = client.get_languages(scope="translation")

targetLanguage = "zh-Hant"
supportedLanguage = False
while supportedLanguage == False:
    if targetLanguage in languagesResponse.translation.keys():
        supportedLanguage = True
    else:
        print("{} is not a supported language.".format(targetLanguage))

# Translate text
if not os.path.exists("abstract.txt"):
    print("abstract.txt文件不存在")
    exit()

inputText = ""
with open("abstract.txt", 'r', encoding="utf-8") as file:
    inputText = file.read()
input_text_elements = [InputTextItem(text=inputText)]
translationResponse = client.translate(content=input_text_elements, to=[targetLanguage])
translation = translationResponse[0] if translationResponse else None
if translation:
    sourceLanguage = translation.detected_language

with open("translated.txt", "w", encoding="utf-8") as translate_file:
    for translated_text in translation.translations:
        translate_file.write(translated_text.text)

print("摘要翻譯已寫入 translated.txt 文件。\n")

############################################## 讀入摘要，進行語音輸出，並將語音輸出存成 .wav 檔。##############################################

import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment
from pydub.playback import play

subscription_key = "8f6f8655f2354e85ade56feb2fb4ef80"
service_region = "eastus"   

input_filename = 'translated.txt'
output_filename = "audio.wav"

speech_config = speechsdk.SpeechConfig( subscription=subscription_key, region=service_region )

# The language of the voice that speaks.
# speech_config.speech_synthesis_voice_name = 'en-US-JennyNeural'
speech_config.speech_synthesis_voice_name = 'zh-CN-XiaoxiaoNeural'  # Chinese voice

# Specify the file name to save the speech
audio_output = speechsdk.audio.AudioOutputConfig( filename = output_filename )
speech_synthesizer = speechsdk.SpeechSynthesizer( speech_config=speech_config, audio_config=audio_output )

# Read text from 'abstract.txt' file
with open(input_filename, 'r', encoding="utf-8") as file:
    text = file.read()

speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("Speech synthesized to 'audio.wav'\n")
    # Play the audio file
    audio = AudioSegment.from_wav(output_filename)
    play(audio)
elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = speech_synthesis_result.cancellation_details
    print("Speech synthesis canceled: {}".format(cancellation_details.reason))
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        if cancellation_details.error_details:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")




