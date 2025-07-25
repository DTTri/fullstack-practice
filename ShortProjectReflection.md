# Project Reflection

## My overall concept understanding of the project

So basically, we're building a smart customer support bot for OptiSigns. But not just any chatbot - one that actually knows what it's talking about because it reads all their help docs and stays up to date.

The whole thing is really three pieces that work together:

- A scraper grabs all the support articles from their website
- An AI that can search through that content and answer questions
- A background job that runs every day to catch any new or updated articles

What's cool about this is that it's not just another generic AI assistant. It actually knows OptiSigns' stuff and can tell you exactly where it got the information from. That's huge for customer support because people need to trust the answers they're getting.

## How I Tackled It

I split this into three parts as the requirements said:

**First - Build the Web Scraper**
I started by figuring out how the OptiSigns support site was structured. Turns out they use a pretty standard help center setup, so I could systematically find all the articles and pull out the good content. I spent extra time making sure it wouldn't break easily because, let's be honest, websites change all the time and nobody wants to babysit a scraper.

**Second - Hook Up the AI**
This was about taking all that scraped content and making it searchable by AI. The tricky part was figuring out how to chunk the content - you need pieces that are small enough for the AI to handle but big enough to actually make sense. I went with splitting by article sections instead of just counting characters because it keeps the logical flow intact.

**Third - Automate the Whole Thing**
The automation was really about being smart with updates - only sending new or changed stuff to OpenAI instead of re-uploading everything every day. I used content hashes and timestamps to figure out what actually changed. This keeps the costs reasonable and makes the whole system actually scalable.

I wanted to build something that could actually run in the real world, not just work for a demo. That meant thinking about what happens when things go wrong, how much it costs to run, and whether someone could actually maintain it.

## How I Learn Something New Like This

I basically just dive in and figure it out as I go, but with some structure.

First thing I do is try to understand what problem we're actually solving. Like, what makes good customer support? How do these vector store things actually work? What's it going to cost to run this thing? I spend time on the basics before jumping into code.

Then I break everything into small pieces I can actually test. I didn't try to build the whole system at once - that's a recipe for disaster. Got the scraper working first, then figured out the AI part, then added the automation. Each piece works on its own, which makes debugging way easier.

I read a lot of docs and looked at examples, but the key thing is understanding why people do things a certain way. Like, why chunk content by headers instead of just character count? Why use these specific OpenAI settings? Once you get the reasoning, you can adapt when stuff inevitably breaks.

Speaking of breaking - debugging taught me the most. When we ran into that Unicode mess or the website started blocking us, I had to really dig into what was happening. That's when you actually learn how things work under the hood.

## Ideas for Making OptiBot Better

**First steps:**

- Make the scraper more bulletproof when websites change
- Handle images and videos in articles better
- Let users give feedback on answers so it gets smarter over time
- Connect it to their existing support ticket system
- Support multiple languages for international customers

**Bigger picture stuff:**

- Suggest helpful articles before people even ask
- Use actual product usage data to give more relevant help
- Add voice support for when people's hands are busy

**The really cool possibilities:**
What if OptiBot could learn from the human support team? Like when a support person gives a great answer that's not in the docs, the system could suggest adding it to the knowledge base. Or if tons of people ask about something that's poorly explained, it could flag that for the content team to fix.

Basically, turn it into a feedback loop where the AI helps improve the documentation, not just answer questions from it.

## What Could Go Wrong

**Technical stuff:**

- The scraper will break when OptiSigns changes their website (not if, when)
- OpenAI costs could get expensive if this thing gets popular
- Response times might slow down as the knowledge base gets huge
- The AI might sound super confident while being completely wrong

**People and business stuff:**

- Customers might not trust AI support yet
- Support staff might worry about being replaced instead of seeing it as a tool

**The real challenge:**
Honestly, I think the hardest part isn't the code - it's the organizational stuff. You need processes to keep the knowledge base current, clear rules about when to hand off to humans, and a company culture that sees AI as helping support staff do better work, not replacing them.

Plus there's the classic AI problem where it makes stuff up but sounds really confident about it. Teaching the system to say "I don't know" when it actually doesn't know is way harder than you'd think.

## Wrapping Up

This was actually a pretty fun project because it felt real. It's not just another AI demo - it's the kind of system you could actually deploy and use.

What I liked most was the automation piece. Keeping AI knowledge bases up to date is usually a huge pain that someone has to do manually. Building the delta detection so it only updates what changed makes the whole thing actually sustainable long-term.

If I kept working on this, I'd probably focus on the user experience next. Like, how do customers actually talk to OptiBot? How do you make it feel helpful instead of annoying? That's probably the make-or-break part for whether people actually use it or just get frustrated and call human support anyway.
