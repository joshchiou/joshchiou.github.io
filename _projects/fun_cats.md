---
layout: page
title: Claire
description: The real senior scientist in the family.
img: assets/img/projects/fun/cats/claire-main.webp
importance: 4
category: fun
images:
  slider: true
---

{% include figure.liquid loading="eager" path="assets/img/projects/fun/cats/claire-main.webp" class="img-fluid rounded z-depth-1 mb-3" alt="Claire" %}

<div class="swiper mySwiper mt-3">
  <div class="swiper-wrapper">
    {% for i in (1..5) %}
    <div class="swiper-slide">
      {% capture img_path %}assets/img/projects/fun/cats/claire-gallery-{{ i }}.webp{% endcapture %}
      {% include figure.liquid loading="lazy" path=img_path class="img-fluid rounded z-depth-1" alt="Claire" zoomable=true %}
    </div>
    {% endfor %}
  </div>
  <div class="swiper-pagination"></div>
  <div class="swiper-button-prev"></div>
  <div class="swiper-button-next"></div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function () {
  new Swiper('.mySwiper', {
    slidesPerView: 1,
    spaceBetween: 16,
    loop: true,
    pagination: { el: '.swiper-pagination', clickable: true },
    navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
    breakpoints: {
      576: { slidesPerView: 2 },
      992: { slidesPerView: 3 }
    }
  });
});
</script>
