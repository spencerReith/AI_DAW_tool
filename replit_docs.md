## Node Docs
Set the REPLICATE_API_TOKEN environment variable

export REPLICATE_API_TOKEN=r8_RKi**********************************

Visibility

Copy
Learn more about authentication

Install Replicate’s Node.js client library

npm install replicate

Copy
Learn more about setup
Run stability-ai/stable-audio-2.5 using Replicate’s API. Check out the model's schema for an overview of inputs and outputs.

import { writeFile } from "fs/promises";
import Replicate from "replicate";
const replicate = new Replicate();

const input = {
    prompt: "Pop, Pop-Electronic, Ballad, Billboard, Drum Machine, Bass, Lush Synthesizer Pads, Synthesizer Arp, Synth Bass, Vocal Sample Chops, Percussion, Honest, Heart-Felt, Melancholic, Vibe, Cool, Modern, Atmospheric, well-arranged composition, 115 BPM",
    duration: 90
};

const output = await replicate.run("stability-ai/stable-audio-2.5", { input });

// To access the file URL:
console.log(output.url());
//=> "https://replicate.delivery/.../output.mp3"

// To write the file to disk:
await writeFile("output.mp3", output);
//=> output.mp3 written to disk

## Python Docs
Set the REPLICATE_API_TOKEN environment variable

export REPLICATE_API_TOKEN=r8_RKi**********************************

Visibility

Copy
Learn more about authentication

Install Replicate’s Python client library

pip install replicate

Copy
Learn more about setup
Run stability-ai/stable-audio-2.5 using Replicate’s API. Check out the model's schema for an overview of inputs and outputs.

import replicate

input = {
    "prompt": "Pop, Pop-Electronic, Ballad, Billboard, Drum Machine, Bass, Lush Synthesizer Pads, Synthesizer Arp, Synth Bass, Vocal Sample Chops, Percussion, Honest, Heart-Felt, Melancholic, Vibe, Cool, Modern, Atmospheric, well-arranged composition, 115 BPM",
    "duration": 90
}

output = replicate.run(
    "stability-ai/stable-audio-2.5",
    input=input
)

# To access the file URL:
print(output.url)
#=> "https://replicate.delivery/.../output.mp3"

# To write the file to disk:
with open("output.mp3", "wb") as file:
    file.write(output.read())
#=> output.mp3 written to disk