---
layout: page
title: Cocktails
description: "Home bartending notes: classic recipes, amaro obsessions, and tiki detours."
img: assets/img/projects/fun/cocktails-peaflower-sour.webp
og_image: /assets/img/projects/og/cocktails-peaflower-sour.jpg
importance: 3
category: fun
images:
  slider: true
---

This started with Swinford Spirits, a creative cocktail lounge in San Diego that I loved and
that closed permanently during the pandemic. With bars shut down, I started making my own
drinks at home, experimenting with different base liquors, infusions, and garnishes, and never
stopped. Current obsessions lean toward stirred drinks: Negroni variations, spec-forward
Manhattans, and anything that involves a good amaro. I have a soft spot for funky rums and
tiki cocktails.

## Favorites

<div class="recipe-grid">
{% for recipe in site.data.cocktail_recipes %}
<div class="recipe-card">
  <div class="recipe-card-header">
    <h3>{{ recipe.name }}</h3>
    <span class="recipe-method">{{ recipe.method }}</span>
  </div>
  <ul class="recipe-ingredients">
    {% for item in recipe.ingredients %}
    <li>{{ item }}</li>
    {% endfor %}
  </ul>
  <p class="recipe-note">{{ recipe.note }}</p>
</div>
{% endfor %}
</div>

## Bars

A few cocktail bars I've liked, close to home and on the road.

<div class="recipe-grid bar-grid">
{% for bar in site.data.cocktail_bars %}
<div class="recipe-card">
  <div class="recipe-card-header">
    <h3>{{ bar.name }}</h3>
    <span class="recipe-method">{{ bar.city }}</span>
  </div>
  <p class="bar-area">{{ bar.area }}</p>
  <p class="recipe-note">{{ bar.note }}</p>
  <a class="bar-map-link" href="https://www.google.com/maps/search/?api=1&amp;query={{ bar.map | url_encode }}" target="_blank" rel="noopener noreferrer">Map <i class="fa-solid fa-arrow-up-right-from-square fa-xs"></i></a>
</div>
{% endfor %}
</div>

## Photos

<div class="swiper cocktail-gallery-swiper mb-4">
  <div class="swiper-wrapper">
    {% for photo in site.data.cocktail_gallery %}
    <div class="swiper-slide">
      <img src="{{ photo.url }}" alt="{{ photo.alt | default: 'Cocktail photo' }}" loading="lazy" decoding="async" style="width:100%;display:block;">
    </div>
    {% endfor %}
  </div>
  <div class="swiper-pagination"></div>
  <div class="swiper-button-prev"></div>
  <div class="swiper-button-next"></div>
</div>

<script>
window.addEventListener('load', function () {
  if (typeof Swiper !== 'undefined') {
    new Swiper('.cocktail-gallery-swiper', {
      slidesPerView: 1,
      pagination: { el: '.cocktail-gallery-swiper .swiper-pagination', clickable: true },
      navigation: {
        nextEl: '.cocktail-gallery-swiper .swiper-button-next',
        prevEl: '.cocktail-gallery-swiper .swiper-button-prev'
      },
      autoHeight: true
    });
  }
});
</script>
