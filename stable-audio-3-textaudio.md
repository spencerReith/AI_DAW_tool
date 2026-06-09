Text-to-Audio
Stable Audio transforms existing audio samples into new high-quality compositions up to six minutes long at 44.1kHz stereo using text instructions.
Try it out
Grab your API key and head over to Open Google Colab or try Stable Audio for free at stableaudio.com.
This endpoint is asynchronous — it returns a generation id immediately (HTTP 202). Poll GET /v2beta/audio/results/{id} to retrieve the result.
Credits
Stable Audio 3.0
Flat rate of 26 credits per successful generation.
As always, you will not be charged for failed generations.
Authorizations:
STABILITY_API_KEY
header Parameters
authorization
required
string non-empty
Your Stability API key, used to authenticate your requests. Although you may have multiple keys in your account, you should use the same key for all requests to this API.
content-type
required
string non-empty
Example: multipart/form-data
The content type of the request body. Do not manually specify this header; your HTTP client library will automatically include the appropriate boundary parameter.
accept	
string
Default: audio/*
Enum: application/json audio/*
Specify audio/* to receive the bytes of the audio directly. Otherwise specify application/json to receive the audio as base64 encoded JSON.
stability-client-id	
string (StabilityClientID) <= 256 characters
Example: my-awesome-app
The name of your application, used to help us communicate app-specific debugging or moderation issues to you.
stability-client-user-id	
string (StabilityClientUserID) <= 256 characters
Example: DiscordUser#9999
A unique identifier for your end user. Used to help us communicate user-specific debugging or moderation issues to you. Feel free to obfuscate this value to protect user privacy.
stability-client-version	
string (StabilityClientVersion) <= 256 characters
Example: 1.2.1
The version of your application, used to help us communicate version-specific debugging or moderation issues to you.
Request Body schema: multipart/form-data
prompt
required
string <= 10000 characters
What you wish the output audio to be. A strong, descriptive prompt that clearly defines instruments, moods, styles, and genre will lead to better results.
You can make a prompt as simple or complex as you like. Simple prompts are good for clean output audio. Complex prompts are good for adding texture and depth to the output audio.
model	
string
Default: stable-audio-3
Value: stable-audio-3
The model to use for generation.
stable-audio-3 requires 26 credits per generation
duration	
number [ 1 .. 380 ]
Default: 190
Controls the duration in seconds of the generated audio.
seed	
number [ 0 .. 4294967294 ]
Default: 0
A specific value that is used to guide the 'randomness' of the generation. (Omit this parameter or pass 0 to use a random seed.)
steps	
integer [ 4 .. 8 ]
Default: 8
Controls the number of sampling steps.
cfg_scale	
number [ 1 .. 25 ]
Default: 1
How strictly the diffusion process adheres to the prompt text (higher values make your audio closer to your prompt). Defaults to 1 if not specified.
output_format	
string
Default: mp3
Enum: mp3 wav
Dictates the content-type of the generated audio.
Responses
202 Generation started. Use the returned id to poll for the result.
400 Invalid parameter(s), see the errors field for details.
403 Your request was flagged by our content moderation system.
422 Your request was well-formed, but rejected. See the errors field for details.
429 You have made more than 150 requests in 10 seconds.
500 An internal error occurred. If the problem persists contact support.

post/v2beta/audio/stable-audio/text-to-audio
Request samples

* Python
* JavaScript
* cURL

Copy

```
import requests, time

response = requests.post(
    f"https://api.stability.ai/v2beta/audio/stable-audio/text-to-audio",
    headers={"authorization": f"Bearer sk-MYAPIKEY", "accept": "audio/*"},
    files={"none": ""},
    data={
        "prompt": "A cinematic orchestral piece with sweeping strings and dramatic brass.",
        "output_format": "mp3",
        "duration": 30,
    },
)

if response.status_code != 202:
    raise Exception(str(response.json()))

generation_id = response.json()["id"]

while True:
    result = requests.get(
        f"https://api.stability.ai/v2beta/audio/results/{generation_id}",
        headers={"authorization": f"Bearer sk-MYAPIKEY", "accept": "audio/*"},
    )
    if result.status_code == 202:
        print("Generation in-progress, retrying in 10 seconds...")
        time.sleep(10)
    elif result.status_code == 200:
        with open("./output.mp3", "wb") as f:
            f.write(result.content)
        break
    else:
        raise Exception(str(result.json()))
```

Response samples

* 202
* 400
* 403
* 422
* 429
* 500
Content type
application/json
Copy
`{`

* `"id": "a6dc6c6e20acda010fe14d71f180658f2896ed9b4ec25aa99a6ff06c796987c4"`
`}`