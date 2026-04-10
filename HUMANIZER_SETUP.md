# Humanizer Skill Setup

The humanizer skill is installed and ready to use in Claude Code. It removes signs of AI-generated writing from text, making responses sound more natural and human-like.

## Installation

The humanizer skill has been cloned to:
```
~/.claude/skills/humanizer/
```

## Usage

### Basic Usage

In Claude Code, invoke the humanizer skill with:
```
/humanizer

[paste your text here]
```

### Voice Calibration

To match your personal writing style, provide a sample of your own writing:
```
/humanizer

Here's a sample of my writing for voice matching:
[paste 2-3 paragraphs of your own writing]

Now humanize this text:
[paste AI text to humanize]
```

## Integration with Insuretechdaily & Career-Ops

The humanizer skill is particularly useful for:

- **Job Evaluations**: Making evaluation reports sound less like AI analysis
- **Cover Letters**: Humanizing generated cover letters before sending
- **Email Communications**: Softening robotic emails to recruiters and companies
- **CV Generation**: Making CV copy sound more personal and authentic
- **Interview Prep**: Naturalizing STAR story formats and talking points

### Example Use Cases

1. **After generating a CV PDF**: Use `/humanizer` to review the cover letter or summary sections
2. **Review evaluation reports**: If job evaluation reports sound too formal/AI-like, humanize key sections
3. **Polish outreach messages**: Before sending LinkedIn messages or emails, run them through the humanizer

## Key Features

The humanizer detects and fixes 29+ AI writing patterns, including:

- **Content Patterns**: Significance inflation, notability name-dropping, superficial analyses
- **Language Patterns**: AI vocabulary, copula avoidance, synonym cycling, passive voice overuse
- **Style Patterns**: Em dash overuse, boldface overuse, title case headings, emoji overuse
- **Communication Patterns**: Chatbot artifacts ("I hope this helps!"), cutoff disclaimers, sycophantic tone
- **Filler and Hedging**: Excessive qualifiers, generic conclusions

## References

- Based on [Wikipedia's "Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- Full documentation: [Humanizer GitHub](https://github.com/blader/humanizer)
