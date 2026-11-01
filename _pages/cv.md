---
layout: profile
title: cv
permalink: /cv/
nav: cv
redirect_from:
  - /resume
---
<h1>cv</h1>
<p class="fl-description">Education and research experience</p>
<section class="fl-cv-block" aria-label="Education"><h3>Education</h3>
{% for education in site.data.cv.education %}<div class="fl-cv-row"><div class="fl-date">{{ education.period }}</div><div><h4>{{ education.degree }}</h4><p>{{ education.institution }}</p><p><em>{{ education.department }}</em></p><ul>{% for advisor in education.advisors %}<li>{{ advisor.label }}: {% include profile/person.html name=advisor.name prefix="Prof. " %}</li>{% endfor %}</ul></div></div>{% endfor %}
</section>
<section class="fl-cv-block" aria-label="Research experience"><h3>Research experience</h3>
{% for experience in site.data.cv.research_experience %}<div class="fl-cv-row"><div class="fl-date">{{ experience.period }}</div><div><h4>{{ experience.role }}</h4><p>{{ experience.institution }}</p><p><em>{{ experience.department }}</em></p><ul><li>{{ experience.focus }}</li><li>{{ experience.advisor.label }}: {% if experience.advisor.name == 'Zheng Zhang' %}{% include profile/person.html name=experience.advisor.name prefix="Dr. " %}{% else %}{% include profile/person.html name=experience.advisor.name prefix="Prof. " %}{% endif %}</li></ul></div></div>{% endfor %}
</section>
