# Stable Audio 2.5 Prompt Guide

With the release of our latest audio model Stable Audio 2.5, we're sharing an updated roundup of our best practices for prompting.

Stable Audio 2.5 is the first audio model designed for enterprise-grade sound production. That means the model introduces capabilities like improved musical structure, faster inference at less than 2 seconds on a GPU, and support for audio inpainting.

The new model is ideal for generating sophisticated, fully developed songs and iterating quickly to create the right sound for every production. With effective prompting techniques, you can get the most out of Stable Audio 2.5's capabilities for use cases like advertising, game soundtracks, and short-form video.

---

## Using Musical Vocabulary

### Consider your use case to ensure creative alignment

Before building your prompt, think about what exactly you want to create. Are you producing audio for an ad campaign and your brand has a certain mood you're going for? Are you scoring the final boss battle in your game and you need the tempo to be fast and exciting?

Each use case will have different musical requirements, from mood to tempo. Start with the end result in mind, and you can build your prompt to get there.

---

### Begin with the three basic building blocks

Start with the essentials of music. Stable Audio 2.5 is designed for generating up to three-minute tracks, so your prompt should include everything you need for a full composition.

The three building blocks below are the simplest — but most important — context to give the model. If you don't specify these things in the prompt, you'll get more random results.

#### Genre/Style
Define the category for your track.

> **Pro tip:** Make sure to clarify your genre references with more specific classifications or subgenres.

| Genres | Subgenres |
|--------|-----------|
| Rock | Classic rock |
| Country | Outlaw country |
| Classical | Contemporary classical |
| Electronic | Ambient house |

#### Tempo (BPM)
Define the speed to match your intended use case and energy level.

> **Pro tip:** If you know the general ranges for your genre of music, the model can adjust to the tempo you want the song to be.

| BPM Range | Description |
|-----------|-------------|
| 60–80 BPM | Slow; good for ballads and blues |
| 80–100 BPM | R&B, house |
| 100–120 BPM | Pop, rock ballads, jazz |
| 120–140 BPM | Disco, upbeat pop, rock, techno |
| 140–160 BPM | Dubstep, metal |

You can also use general tempo terms: Slow, Medium, Building, Fast.

#### Overall Mood
Establish the emotional foundation of your track.

> **Pro tip:** Use clear, descriptive emotional terms that go beyond simple words like "happy" and "sad."

- **Primary emotion** → "euphoric" instead of "happy"
- **Secondary emotions** → "melancholic" instead of "sad"
- **Energy level** → "soaring" instead of "energetic"
- **Atmosphere** → "mystical" instead of "weird"

**Example prompt:**
> *"A relaxing Bossa Nova instrumental, perfect for an elevator. The mood is smooth, patient, and relaxing, 115 BPM."*

---

### Layer in more musical elements to build depth

Specify the important sound sources in your track, then go beyond that with more detail on texture and production characteristics. A common challenge is generating a track that sounds too generic or flat — add more specific musical elements to get a richer, more dynamic composition.

#### Primary Instruments
These carry the melody or main musical theme and are the focal point listeners typically follow.

- Piano
- Synthesizer
- Electric guitar
- Violin

#### Supporting Instruments or Elements
These complement the main melody, usually mixed in the background or at moderate levels.

- Bass lines
- String section
- Electric piano

#### Rhythm Components
Define the percussive elements that drive your track.

- 808 drum machine
- SP-1200
- Syncopated percussion
- Break drums

#### Texture Elements
Add layers that create sonic depth and atmosphere.

- Jazz improvisation
- Atmospheric pads
- Reverb tails and echoes
- Countermelodies and harmonies

#### Production Characteristics
These elements describe how the track is recorded, mixed, and produced.

> **Pro tip:** You don't always want a polished studio sound. For example, a lo-fi hip hop track calls for a relaxing, nostalgic feel that requires a vintage recording quality. Play around with different production styles to get the feel you're going for.

**Recording quality descriptors:** Studio-quality/pristine, Lo-fi/bedroom-recorded, Lush, Textured, Vintage/analog

**Arrangement style:** Expansive, Layered, Minimalist

**Sonic characteristics:** Modern, Raw, Stripped-back

**Example prompt:**
> *"An exciting breakbeat instrumental perfect for fast-paced video games, featuring funky electric guitar chords, steady break drums, smooth electric piano, and supporting bass. The mood is fresh, modern, and adventurous, 105 BPM."*

---

### Recap: Prompt checklist

For best results, your prompt should include:

- Specific genre classification
- Sophisticated mood descriptors
- Appropriate BPM for the genre
- Detailed instruments (primary, secondary, rhythm, and texture)
- Additional production characteristics

---

## Prompt Construction Techniques

### Order matters in your prompt

Start with the core style and genre, then the key musical elements. Structure your prompt in this order:

1. Core style/genre
2. Key instruments and musical elements
3. Mood and emotion
4. Specific details
5. Additional instructions

**Good structure:**
> *"Cinematic outlaw country instrumental perfect for a long drive featuring a blues pedal steel guitar, a rustic mandolin, a fiddle playing call and response, a tape-driven rattly drum-kit, an autoharp, and a soaring accordion solo. The mood has southern soul, is raw, emotional, expansive, and full of the blues."*

**Less effective:**
> *"Make a song that's happy and has guitar, fiddle and drums"*

To iteratively improve, start with the basic prompt and evaluate the result. Identify any missing elements, add more specific instructions, and retry as needed.

---

### Advanced tips for refinement

#### 1. Use titles to give direction
Adding a title to your prompt provides clear and immediate context for the mood and direction of your song. For example, adding *"titled 'Rebellion'"* or *"titled 'On & On'"* gives the model an interesting direction for the mood. This simple addition can improve the musicality of your results.

#### 2. Incorporate geographic context
If your desired sound is associated with a real-world location, include it in your prompt. This helps the model understand the cultural and historical influences of the music. For instance, if you're creating a House track, specifying "Chicago," "New York," "Detroit," or "Ibiza" will steer the model toward the distinct styles and characteristics of that region.

#### 3. Define a use case
Clarify the intended use or scenario for your song. Adding a phrase like *"perfect for opening credits"* or *"perfect for a long drive"* gives the model a functional purpose for the music, helping it create a track that fits a specific narrative or mood.

**Example prompt:**
> *"A luxurious indietronica instrumental perfect for a perfume advertisement featuring clean guitars, synthesizers, and a slow-tempo drum machine pattern."*

#### 4. Use original and precise language
Use a variety of descriptive words and avoid repeating the same adjectives. Use a range of vocabulary that cohesively fits a musical context — for example, *"smooth electric piano"* or *"textural percussion"* provide rich, detailed information. This maximizes the context you provide and ensures every word counts.

It also helps to reference eras to describe musical and production elements, such as *"80s gated reverb"* or *"90s grunge distortion."*

**Example prompt:**
> *"90s garage rock instrumental with a grunge influence featuring poppy distorted guitars, frantic and energetic drums and tube-distorted bass guitar."*

#### 5. Try inpainting
Stable Audio 2.5 supports audio inpainting, which is useful for preserving an original part of a song while generating variations. Advertising professionals, for example, might generate different versions of a song to match different creative in a campaign.

Inpainting allows you to:

- Upload existing audio *(Note: Terms of Service require that uploads be free of copyrighted material; advanced content recognition is used to maintain compliance)*
- Select starting points for generation
- Let the model complete the composition using context

If you're aiming for a specific section to be inpainted, specify the start and end time. The more context provided before it, the more the model uses that as an example. The prompt structure is the same as normal prompting.

**Example prompt:**
> *"A soulful tech-house song with beautiful and melancholic undertones and epic breakdowns, noisy granular synthesizer layers, and epic reverberating and echoing leads."*