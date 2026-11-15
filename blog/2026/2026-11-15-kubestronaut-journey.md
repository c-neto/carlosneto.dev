---
tags: kubernetes, certification
date: "2026-11-15"
category: Kubernetes
author: Carlos Neto
title: "Kubestronaut: My Honest Journey (Including Procrastination and a Retake)"
description: "How I became a Kubestronaut: a year of procrastination, six focused months, failing the CKS by one point, and the study routine and exam order I recommend."
myst:
  html_meta:
    description: "How I became a Kubestronaut: a year of procrastination, six focused months, failing the CKS by one point, and the study routine and exam order I recommend."
og:title: "Kubestronaut: My Honest Journey (Including Procrastination and a Retake)"
og:description: "How I became a Kubestronaut: a year of procrastination, six focused months, failing the CKS by one point, and the study routine and exam order I recommend."
---

*__Blog Post Publish Date:__ 2026/11/15*

---

# Kubestronaut: My Honest Journey (Including Procrastination and a Retake)

This post is an honest account of how I passed the five CNCF Kubernetes certifications (CKA, KCNA, KCSA, CKAD, and CKS) and became a Kubestronaut. I share how I overcame a year of procrastination and why I failed the CKS even though I was prepared for it. I also cover the study routine and methods that worked for me, what each exam asks for, and the order I recommend for your professional profile.

__DISCLAIMER:__ Everything in this post comes from my own experience, in my context and my life. Don't take it as an absolute recommendation. I'm not trying to say what is "right", only to share what I went through. What worked for me might not work for you.

## Why I Went for the Kubestronaut Title

When I started the Kubestronaut path, I had been working with Kubernetes every day for more than five years. Even with that experience, I still lacked knowledge in areas covered by the certifications but outside the scope of my work. That was my main motivation, and the exam curriculum gave me a study roadmap to fill those gaps. Besides helping me learn, the certifications can open doors to jobs that require them and help me network within the cloud native community.

It's important to keep in mind that knowing a subject is different from mastering it. Knowing means you understand which tools exist to solve a problem and how to use them. Mastering means you have the practical experience to pick the solution closest to ideal for a given context, and that only comes with time and real work. A certification says you know Kubernetes. It doesn't say you master it.

So I disagree with the idea that these certifications are only for people who already master Kubernetes. They suit people who are learning it even better. If I knew nothing about Kubernetes today, I would study for the certifications instead of watching random YouTube videos. The curriculum makes the learning curve more organized and much less tortuous.

## What to Expect From Each Exam

All five exams are taken remotely on [PSI Bridge](https://www.psiexams.com/test-owners/test-delivery/online-proctoring/), with webcam monitoring and a room scan at check-in, and include one free retake. KCNA and KCSA have 60 multiple-choice questions, with no references allowed, and the result arrives by email right away. CKA, CKAD, and CKS have 15 to 20 hands-on tasks in a terminal on a remote Linux desktop, with access to the official docs, and the result takes up to 24 hours. They also include two [Killer Shell](https://killer.sh/) simulator sessions, which match the exam closely but run faster, so expect a slower terminal on exam day. For more details about the proctoring, see the [Candidate Handbook](https://docs.linuxfoundation.org/tc-docs/certification/lf-handbook2/taking-the-exam).

Because the hands-on exams let you open the official documentation, don't try to memorize everything. Learn to do the tasks using the docs as a guide, and remember where each piece of information lives.

Here is what each exam covers:

| Exam | Format | Duration | Pass Score | OpenBook |
| --- | --- | --- | --- | --- |
| [KCNA](https://training.linuxfoundation.org/certification/kubernetes-cloud-native-associate/) | multiple choice | 90 minutes | 75% | No |
| [KCSA](https://training.linuxfoundation.org/certification/kubernetes-and-cloud-native-security-associate-kcsa/) | multiple choice | 90 minutes | 75% | No |
| [CKAD](https://training.linuxfoundation.org/certification/certified-kubernetes-application-developer-ckad/) | hands-on | 2 hours | 66% | Yes |
| [CKA](https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/) | hands-on | 2 hours | 66% | Yes |
| [CKS](https://training.linuxfoundation.org/certification/certified-kubernetes-security-specialist/) | hands-on | 2 hours | 67% | Yes |

**KCNA (_Kubernetes and Cloud Native Associate_):** is for people starting with Kubernetes. It asks conceptual questions like "what is a Pod?", "which component decides on which node a Pod runs?", or "what is the difference between a Deployment and a StatefulSet?". If you already work with Kubernetes, even at a junior level, you'll pass it with your eyes closed.

**KCSA (_Kubernetes and Cloud Native Security Associate_):** is the same idea applied to security. It's easy for a SecOps engineer, but a DevOps engineers shouldn't underestimate it. Expect questions like what an SBOM is, which Pod Security Standard blocks privileged containers, or what the 4Cs of cloud native security are. Gaps like these are why I wanted the Kubestronaut path.

**CKAD (_Certified Kubernetes Application Developer_):** is the simplest of the hands-on exams and covers using a cluster: exposing a Deployment with a Service, adding a liveness probe, mounting a ConfigMap, scheduling a CronJob, or installing a Helm chart. The name is misleading, since you write no code beyond a trivial Bash script. "Application Developer" means someone who deploys an application to a working cluster, not someone who writes Operators.

**CKA (_Certified Kubernetes Administrator_):** covers everything in the CKAD plus provisioning and operating the cluster, configuring the kubelet, upgrading the cluster, fixing a broken control plane component, or granting namespace access with a Role and a RoleBinding. Troubleshooting is the biggest part of the exam.

**CKS (_Certified Kubernetes Security Specialist_):** isn't hard, but it covers the most topics and tools, none of them deeply, default-deny NetworkPolicies, AppArmor and seccomp profiles, image scanning and signature checks, Falco, and API server audit logs. My one complaint is the CKA prerequisite. One of my CKS tasks was a cluster upgrade, which felt like CKA material, and the KCSA would make a better prerequisite for a security track.

> _From February 15, 2027, Kubestronaut will also require the [CKNE](https://training.linuxfoundation.org/resources/kubestronaut-program/), and two AI certifications, [KAIA and CKIE](https://www.cncf.io/announcements/2026/11/10/cncf-launches-certified-kubernetes-network-engineer-certification-ckne-to-advance-production-ready-networking-skills-for-ai-era/), are planned for 2027. I'd leave new exams for last._

## Kubestronaut Benefits and How to Keep the Title

When you become a Kubestronaut, you get an exclusive jacket, a Credly badge, and access to a private Slack channel and mailing list. Your photo also goes on the [Kubestronaut page](https://www.cncf.io/training/kubestronaut/), which lists everyone who holds the title ([here is mine](https://www.cncf.io/training/kubestronaut/?_sf_s=carlos%20neto)). Every year, you also get five 50%-off certification coupons, which you can use yourself or share, and 20% off three [CNCF events](https://www.cncf.io/events/), such as [KubeCon](https://www.cncf.io/kubecon-cloudnativecon-events/) or [KubeDays](https://www.cncf.io/blog/2022/08/17/introducing-kubeday-event-series-kicking-off-with-kubeday-japan-this-december/). The full list is on the [Kubestronaut Program page](https://training.linuxfoundation.org/resources/kubestronaut-program/).

From what I've seen and talked about with colleagues, the market uses these certifications mostly to speed up interviews. They also help you rank higher when tech recruiters search on LinkedIn and strengthen your position when negotiating a contract. They signal that you know the Kubernetes basics, and some companies go further and list them as a requirement in their job openings.

The Kubestronaut title isn't permanent, though. Each certification is valid for two years, and according to the [Kubestronaut FAQ](https://www.cncf.io/training/kubestronaut/kubestronaut-faq/), all of them must be active at the same time. When the first one expires, you keep the title until the end of that year. If you don't renew by then, you lose the title and its benefits.

## Which Exam to Take First

I took the exams in a poorly planned order: CKA, KCNA, KCSA, CKAD, and then CKS. There was no logic behind it, and that is one of the reasons I wrote this post. If I were starting again, I'd pick a path based on my role:

<img src="/_static/2026/2026-11-15/kubestronaut-exam-paths.svg" alt="Diagram of the Kubernetes certification order I recommend for junior DevOps, senior DevOps, SecOps, and Kubestronaut candidates" loading="lazy" width="960" height="330" style="max-width: 100%; height: auto;">

A junior DevOps engineer gets a solid foundation going from the KCNA to the CKAD and then the CKA. If you're a mid-level or senior DevOps engineer and want only one, take the CKA. I don't recommend taking only the CKAD. The CKA covers everything in the CKAD, so preparing for the CKA also prepares you to pass the CKAD with little extra study, and taking the CKAD later becomes easy if you want it. If you're in SecOps, start with the KCSA, then the CKA (unfortunately, because of the CKS prerequisite), then the CKS. And for the Kubestronaut title, go from the easiest to the hardest: KCNA, KCSA, CKAD, CKA, and CKS.

## How to Pay Less for the Exams

The Linux Foundation charges the same dollar price everywhere, without purchasing power parity (PPP) pricing. Besides single exams, it sells bundles for specific tracks, such as the [Kubestronaut Bundle](https://training.linuxfoundation.org/certification/kubestronaut-bundle/) with every exam the title requires, and upgrade bundles for people who already hold the [CKA](https://training.linuxfoundation.org/certification/cka-to-kubestronaut-upgrade-bundle/) or the [CKAD](https://training.linuxfoundation.org/certification/ckad-to-kubestronaut-upgrade-bundle/). For a security track, there are the [KCSA + CKS](https://training.linuxfoundation.org/certification/kubernetes-and-cloud-native-security-associate-kcsa-certified-kubernetes-security-specialist-cks-exam-bundle/) and [CKA + CKS](https://training.linuxfoundation.org/certification/cka-cks-exam-bundle/) bundles. Smaller combinations include the [KCNA + CKA](https://training.linuxfoundation.org/training/kcna-cka-exam-bundle/) and the [CKA + CKAD + CKS](https://training.linuxfoundation.org/training/cka-ckad-cks-exam-bundle/). The bundles vary over time, so check the current offer on the [Kubestronaut Program page](https://training.linuxfoundation.org/resources/kubestronaut-program/) and the Linux Foundation store before buying.

Don't pay the full price. Wait for a promotion. In my experience, October and November usually bring discounts of up to 30% ~ 50%. Bundles also tend to get a better discount than buying each exam separately.

So before buying anything, define the track of certifications you want. If it's a full track, buy its bundle. If you want only one certification, buy that single exam. Buying a bundle without knowing what you want from the certifications puts an unnecessary weight on you.

People often tell me the exams are expensive, and they are, especially if you don't earn in US dollars. Still, the fee is the cheap part. The hours of study and the mental energy they drain cost much more.

## From Procrastination to a Study Routine

Before the six months in which I passed everything, I procrastinated for a whole year. I would start studying, stop, come back weeks later, and remember nothing. Every restart, I had forgotten the imperative kubectl commands and had to learn them again.

What changed was the gym. I have trouble with focus, and starting a regular exercise routine trained the discipline I then used to study. I only managed to finish the certifications because I started going to the gym at the same time. Running, walking, or any regular sport should work the same way.

The routine that worked for me was one hour a day. Not two, not three. A five-hour rush on Sunday doesn't make you learn. I kept one day a week, usually Sunday, without studying. And I stopped negotiating with myself: "I won't study today, but tomorrow I'll do two hours" is the beginning of failure.

Two more habits helped. I didn't keep checking the course progress bar, because that only triggered anxiety. And I stopped telling people I was studying for a certification. Our brain is dumb: when we announce that we're doing something, it feels like we already did it. There's research behind this. Peter Gollwitzer and colleagues ran four experiments on identity-related intentions, such as studying law to become a lawyer, and published them in Psychological Science. When other people took notice of the intention, participants acted on it less than those whose intention was ignored. Being noticed gave them a premature sense of already having that identity ([Gollwitzer et al., 2009](https://doi.org/10.1111/j.1467-9280.2009.02336.x)). Finish the exam first, then show it off.

Finally, I used a single study source: the [KodeKloud](https://kodekloud.com/) courses. That choice surprised me, because I've always struggled with video courses. I lose focus quickly, so I've always studied from physical books, on paper, away from notifications and from the quick glances at email, WhatsApp, and Instagram that feed you cheap dopamine. Even with that resistance, I loved KodeKloud. I'm not paid to say this, but they are the best courses I've ever taken: a video lesson, then a lab prepared only to practice what the lesson covered, with no distractions. Every lesson also has a full text transcript and translated subtitles.

KodeKloud also publishes its courses as text on [KodeKloud Notes](https://notes.kodekloud.com/), such as the [CKS course](https://notes.kodekloud.com/docs/Certified-Kubernetes-Security-Specialist-CKS/index#course-certified-kubernetes-security-specialist-cks). The best part is that the text version is free and doesn't require a subscription. I switched to it on the days I was tired of watching videos. Every topic in the course is worth studying, especially the ones that aren't on the exam, such as TLS.

When a topic was hard for me to understand, I talked about it with ChatGPT in voice mode until it made sense. Saying the question out loud and going back to the part I still didn't get helped me understand concepts that were difficult for me. It also let me express my frustration with the topic, almost like venting.

## How I Prepared for the CKA, CKAD, and CKS

Don't overestimate yourself. If you're an experienced DevOps engineer who knows Kubernetes well and thinks you'll pass easily, be careful. In the exam there's no Google, no AI, and no IDE you're used to. Maybe you don't need to study Kubernetes, but you definitely need to study for the exam. Knowing how to do everything isn't enough. You need to do everything fast, in Vim, in a laggy remote terminal, with the clock in your head. The exam has no trick questions. It's well designed and reasonably difficult, but it requires solid preparation, and you can't pass it after studying for a weekend.

The labs mattered more than just watching videos. For my final preparation, I redid all the KodeKloud mock exams until I got 100% right, no matter how many attempts it took. After that, I repeated the two Killer Shell sessions until I got them right, too. Because each session expires 36 hours after activation, I reserved a weekend for each one. The best sign that you are ready is scoring 100% on both Killer Shell sessions on autopilot, without stopping to think, with about 30 minutes left on the clock. If you get there, you will pass the exam.

I also used [CK-X](https://github.com/sailor-sh/CK-X), an open source project that runs a Killer Shell-like simulator locally with Docker Compose, for free. It helped me a lot. Practice questions are never too many, so I also used the [CKS exam guide](https://devsecops.puziol.com.br/kubernetes/cks/exam/) and [solved CKS questions by David Puziol](https://devsecops.puziol.com.br/category/cks-quest%C3%B5es-resolvidas/).

One thing I would skip: a home lab. I bought a mini PC on AliExpress, installed Proxmox, and built base images for my cluster. I spent more time fighting Proxmox and networking than practicing Kubernetes, while the course labs were ready to use.

Drill the imperative kubectl commands until they're automatic, because they generate resources and YAML much faster than writing manifests by hand. Learn Vim too. You only need it to edit YAML, but you need to do that well, and I wrote [Vim for Kubernetes Certification Exams](/blog/2026/2026-07-15-vim-kubernetes-exams.md) about the techniques I used. Finally, prepare your workstation. Keyboard layouts and shortcuts can break you, especially on a MacBook with a Brazilian layout, where a dead key can stop you from typing `~` in `cd ~/Documents`. My checklist is in [Workstation Setup for Kubernetes Exams](/blog/2026/2026-07-09-workstation-setup-kubernetes-exams.md).

## Failing the CKS by One Point

The CKS passing score is [67%](https://docs.linuxfoundation.org/tc-docs/certification/faq-cka-ckad-cks). On my first attempt, I scored 66%.

During the exam, I got stuck on a task to configure Docker to expose the runtime over TCP instead of the Unix socket. I knew how to do the rest of the exam, but I didn't know that one at first, and I kept insisting on it. When I noticed the time, I had about 10 tasks left and less than 60 minutes. If a task is on a topic you don't master, skip it and come back later.

But perfectionism wasn't the only cause. For every exam, I keep a rule: the day before, I don't touch the computer, stay fully offline, and don't study. A hands-on exam needs a rested mind. For the first CKS attempt, I broke that rule. I spent about eight hours on Sunday redoing every lab, and on Monday at 8 AM I was tired and making simple mistakes.

On the second attempt I followed my rule and passed with 81%. My suggestion is to schedule the exam for Monday morning, with Sunday free: sleep a lot, go to the mall, have an ice cream. On a Monday morning, your mind isn't yet filled with work problems.

If you fail, you're not a failure. You get the chance to prepare more and end up knowing more than someone who passed by luck. Failing would be giving up or going back to procrastinating.

## Was It Worth It?

I really enjoyed the Kubestronaut journey. It cost me a lot of energy and some sacrifices in my personal life, but it was an enriching experience. Besides learning topics I don't use at work, it made me a more resilient person. Some topics are fun and some are very boring, and you have to accept both. If you're still thinking about it, buy the exam and do it.

I reserve a special thanks for my former coworker and Golden Kubestronaut [Mateus Müller](https://www.linkedin.com/in/mateus-gabriel-m%C3%BCller-790709bb/), who helped me structure my studies and gave me tips about the exams.

## Key Takeaways

- A certification proves knowledge, not mastery.
- The real cost is study time and mental energy, not the fee.
- Define the track, then buy its bundle on promotion.
- Study one hour a day, with one day off. The gym helps with focus.
- Use one study source: KodeKloud courses, with free text versions on KodeKloud Notes.
- Prioritize hands-on practice under exam conditions: imperative kubectl, Vim, and the official docs.
- Ready for the exam means 100% on both Killer Shell sessions with 30 minutes to spare.
- Skip the home lab. Spend your time on Kubernetes, not on Proxmox and virtualization.
- Rest the day before the exam, and schedule it for Monday morning, before work.

## References

- [Kubestronaut Program (Linux Foundation)](https://training.linuxfoundation.org/resources/kubestronaut-program/)
- [Kubestronaut FAQ (CNCF)](https://www.cncf.io/training/kubestronaut/kubestronaut-faq/)
- [Multiple Choice Exams: Frequently Asked Questions (Linux Foundation)](https://docs.linuxfoundation.org/tc-docs/certification/faq-mc)
- [Frequently Asked Questions: CKA, CKAD, and CKS (Linux Foundation)](https://docs.linuxfoundation.org/tc-docs/certification/faq-cka-ckad-cks)
- [Important Tips: CKA and CKAD (Linux Foundation)](https://docs.linuxfoundation.org/tc-docs/certification/tips-cka-and-ckad)
- [Important Instructions: CKS (Linux Foundation)](https://docs.linuxfoundation.org/tc-docs/certification/important-instructions-cks)
- [Certification Resources Allowed (Linux Foundation)](https://docs.linuxfoundation.org/tc-docs/certification/certification-resources-allowed)
- [Kubernetes and Cloud Native Associate (Linux Foundation)](https://training.linuxfoundation.org/certification/kubernetes-cloud-native-associate/)
- [Kubernetes and Cloud Native Security Associate (Linux Foundation)](https://training.linuxfoundation.org/certification/kubernetes-and-cloud-native-security-associate-kcsa/)
- [CNCF Launches Certified Kubernetes Network Engineer (CKNE) (CNCF, 2026)](https://www.cncf.io/announcements/2026/11/10/cncf-launches-certified-kubernetes-network-engineer-certification-ckne-to-advance-production-ready-networking-skills-for-ai-era/)
- [CK-X Simulator (GitHub)](https://github.com/sailor-sh/CK-X)
- [When Intentions Go Public: Does Social Reality Widen the Intention-Behavior Gap? (Psychological Science, 2009)](https://doi.org/10.1111/j.1467-9280.2009.02336.x)

---

> *I'm Carlos Neto, and this blog is a brain dump of my career experience. More about me on [my home page](/index.md). If you have questions or a different approach, contact me on [LinkedIn](https://www.linkedin.com/in/c-neto/) or leave a comment below.*

---

```{raw} html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "BlogPosting",
      "headline": "Kubestronaut: My Honest Journey (Including Procrastination and a Retake)",
      "description": "How I became a Kubestronaut: a year of procrastination, six focused months, failing the CKS by one point, and the study routine and exam order I recommend.",
      "datePublished": "2026-11-15",
      "inLanguage": "en",
      "url": "https://carlosneto.dev/blog/2026/2026-11-15-kubestronaut-journey/",
      "mainEntityOfPage": "https://carlosneto.dev/blog/2026/2026-11-15-kubestronaut-journey/",
      "image": "https://carlosneto.dev/_static/2026/2026-11-15/kubestronaut-exam-paths.svg",
      "keywords": ["Kubernetes", "Kubestronaut", "CKA", "CKAD", "CKS", "KCNA", "KCSA", "Kubernetes certification"],
      "author": {"@id": "https://carlosneto.dev/#person"}
    },
    {
      "@type": "Person",
      "@id": "https://carlosneto.dev/#person",
      "name": "Carlos Neto",
      "url": "https://carlosneto.dev/",
      "sameAs": ["https://www.linkedin.com/in/c-neto/", "https://github.com/c-neto"]
    },
    {
      "@type": "BreadcrumbList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://carlosneto.dev/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://carlosneto.dev/blog/"},
        {"@type": "ListItem", "position": 3, "name": "Kubestronaut: My Honest Journey (Including Procrastination and a Retake)"}
      ]
    }
  ]
}
</script>
```
