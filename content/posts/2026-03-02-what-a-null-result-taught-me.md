---
title: What a Null Result Taught Me
date: 2026-03-02
excerpt: I spent four months preparing a study and measured nothing. Looking back, I had confused what I cared about with what I could measure.
tags: Method, Research notes
---

Last autumn I designed a study to test something that seemed obvious to me: adding dynamic distractors to the first level of a puzzle game should slow down how fast players form a correct mental model.

Forty participants. Nothing. Completion time, error counts, post-hoc questionnaire — all of it sat inside the noise.

## The first instinct is the wrong one

My first instinct was that the sample was too small. This is almost always the first instinct, and it is almost always wrong. After running a post-hoc power analysis I had to admit it: at the effect size I actually observed, reaching significance would take more than three hundred people. Which is to say that even if a difference exists, it is too small to matter for design.

## The real problem was operationalization

Going back over it, I realized the thing I cared about was *when a player **understands** the rule*. What I measured was *when a player **finishes** the level*.

Those two are much further apart than I assumed. A player can complete a level by brute force without understanding the mechanic at all, or understand it thirty seconds in and still lose two minutes to clumsy inputs. My dependent variable mixed both kinds of people together, and then I expected to read a difference in comprehension speed out of the mixture.

> Measurement is not the last step of a study. It is part of designing the hypothesis, and it has to be settled at the same time.

## What I do first now

Starting a study now, I force myself to answer three questions and skip none of them:

- If my hypothesis is right, **which specific number moves**? In which direction?
- Could that number also move for reasons unrelated to the hypothesis?
- How exactly am I going to rule those reasons out?

The third is the easiest one to hand-wave. I used to write "controlled by random assignment" and walk away satisfied. Random assignment controls systematic differences between groups. It does nothing about a dependent variable that is a mixed signal to begin with.

## It wasn't a total loss

I eventually looked at that data another way: not completion time, but **whether a player, having once performed an action correctly, ever got it wrong again**. That measure is far cleaner, and it did show a small difference between groups. It was not enough to carry a paper, but it became the pilot for [the CHI paper](../publications.html).

A study that measures nothing isn't wasted if it makes you ask the question more precisely. Though at the time it did sting.
