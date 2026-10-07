---
# HOW TO ADD A PROJECT
# 1. Create a folder in content/projects/, e.g. content/projects/my-robot/
#    (the folder name becomes the address: pedrocordero.hu/projects/my-robot/)
# 2. Copy this file into it and rename it to index.md
# 3. Put the project's images in the same folder and fill in the fields below.
# Lines starting with # are notes and can be deleted.

title: Project title
summary: One or two sentences. Shown on the project card and in search results.
date: 2025-01-31            # used to sort projects, newest first
cover: ./cover.webp         # optional: image in this folder, shown on the card and at the top
tags: [Python, ROS2]        # optional
links:                      # optional: buttons under the title
  - label: Code
    url: https://github.com/PedroCordero/your-repo
  - label: Paper
    url: https://doi.org/...
featured: false             # true = shown on the home page
draft: false                # true = hidden from the site (work in progress)
---

Write the project here in normal Markdown.

## A section

Images in this folder: ![Description](./diagram.webp)

*A line in italics right after an image is shown as its caption.*

Videos go in public/media/ and are embedded like this:

<video src="/media/my-robot-demo.mp4" autoplay loop muted playsinline></video>
