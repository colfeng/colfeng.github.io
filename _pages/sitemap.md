---
layout: profile
title: Sitemap
permalink: /sitemap/
---

<h1>sitemap</h1>
<section class="fl-content-block">
<ul>{% for item in site.data.profile_navigation %}<li><a href="{{ item.url | relative_url }}">{{ item.label }}</a></li>{% endfor %}</ul>
<p><a href="{{ '/sitemap.xml' | relative_url }}">XML sitemap</a></p>
</section>
