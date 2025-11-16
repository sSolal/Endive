# Contributing to Endive <3

Welcome! So you want to help build a proof assistant based on rewriting? Excellent choice. Pull up a chair, grab a hot cocoa, and let's talk about how you can join us.

## The Bar Is Low, The Fun Is High

This is an early-stage project, which means we're still figuring things out and that's the exciting part! Your contributions, big or small, help shape what Endive becomes. No need to be a category theory wizard or a formal methods expert. If you're curious and willing to tinker, you're already qualified.

## Ways to Contribute

There are so many ways to help! Pick what sounds fun to you:

### Build New Helpers
Helpers make Endive more usable. They're modular components that extend what Endive can do. Check out `src/engine/helpers/` to see existing ones (like `alias.py` and `goal.py`), and feel free to build your own! Ideas include:
- Suggestions for next proof steps
- Better error messages
- Computing terms
- Automatical proof steps
- AI integration?
- Plot generator
- Proof tree visualization
The list is endless!

### Create Math Libraries & Examples
Endive needs more pre-built mathematical knowledge! Contribute `.end` files with:
- Common theorems and proofs
- Interesting mathematical structures
- Tutorial examples for newcomers
- Worked-out demonstrations

Put them in the `examples/` directory so others can learn from them.

### Red Team the Logic
Here's a fun one: **try to break Endive**. Start with true axioms and see if you can prove something false. If you succeed, you've found a critical bug! This is both useful and oddly satisfying when it works.

### Hunt Bugs
Found something weird? An error message that doesn't make sense? A reduction that should work but doesn't? Report it! Even better, try to fix it. Every bug report helps, even if you're not sure if it's really a bug.

### Build Roadmap Features
Check out `ROADMAP.md` for features we're planning or are dreaming to develop. Or look at the TODO comments in the code. Pick something that seems interesting and give it a shot!

### Explore Wild Use Cases
Can Endive be used for something other than formal proofs? For fields outside of computer science? Let your imagination run wild!

### Solidify the Math
If you're into the theory side, help strengthen Endive's mathematical foundations. There's a lot of work to do in writing up explanations, finding edge cases in the reduction rules, proving properties about the system, relating it to existing literature...

## Getting Started

Setting up Endive is delightfully simple:

```bash
# 1. Clone the repo
git clone <repo-url>
cd Endive

# 2. (Optional) Make a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install in development mode
pip install -e .

# 4. Try it out!
python main.py

# 5. Run in debug mode to see what's happening
python main.py --debug

# 6. Run the tests
python main.py --test
```

No external dependencies. Just Python 3.8 and your enthusiasm.

## Adding Integration Tests

Before contributing code changes, please add tests! Endive uses a custom integration test format with `.end` files.

### How It Works

Integration tests live in `tests/` and use the `.end` extension. The special syntax is:

```
statement ~ expected result
```
Or, if a test should fail,
```
statement ~ error # expected result

The `~` separates what you're testing from what you expect to happen.

### Test Examples

**Testing that something succeeds:**
```
Define foo, bar
Check foo ~ success
```

**Testing with expected output:**
```
Goal A => B
Start A => B ~ success # Goal A => B is reachable
```

**Testing that something fails:**
```
Check nonexistent ~ error # undefined
```

### Running Your Tests

```bash
python main.py --test
```

The test runner will process all `.end` files in `tests/` and report which passed or failed.

### Where to Put Your Tests

- **New helper?** Create `tests/your_helper_name.end`
- **Bug fix?** Add a test that would have caught the bug
- **New feature?** Add tests showing it works as intended

## Project Structure

Of course, check the most up to date project structure in the `README.md` file before commiting anything!

## Submitting Your Contribution

1. **CLone** the repository
2. **Create a branch** with a descriptive name (`git checkout -b add-plotting-helper`)
3. **Make your changes** (and add tests!)
4. **Run the test suite** to make sure everything still works
5. **Commit** with a clear message explaining what and why
6. **Open a Pull Request** and describe what you've done

We'll review it together and iterate if needed. PRs are conversations, we will be happy to look at anything!

## Need Help?

Stuck? Confused? Not sure if your idea makes sense? **Just ask :)** Open an issue, start a discussion, or add a comment to an existing thread. There are no silly questions when you're exploring new territory.

Remember: Endive is young, the community is friendly, and we're all learning together. Your contribution, no matter how small, makes this project better.

Happy rewriting!
