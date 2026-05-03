/**
 * api_override.js — «Фронтовой альбом»
 *
 * Переопределяет функции, которые раньше работали с localStorage,
 * заменяя их запросами к Django API.
 *
 * Этот скрипт загружается ПОСЛЕ основного скрипта сайта,
 * поэтому его функции перекрывают оригинальные.
 *
 * Функции, которые переопределяются:
 *   afSaveHero      → POST /api/heroes/
 *   afSaveKhronika  → POST /api/khronika/
 *   afSaveLetter    → POST /api/letters/
 *   afDelCard       → DELETE /api/{heroes|khronika|letters}/{uid}/
 *   DOMContentLoaded → GET /api/{heroes|khronika|letters}/
 */

(function () {
  'use strict';

  /* ── Читаем CSRF-токен из cookie (Django устанавливает его автоматически) ── */
  function getCsrf() {
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? m[1] : '';
  }

  /* ── Базовый fetch с CSRF-заголовком ── */
  function apiFetch(url, options) {
    options = options || {};
    options.headers = Object.assign(
      { 'X-CSRFToken': getCsrf() },
      options.headers || {}
    );
    options.credentials = 'same-origin';  // нужно для сессионной cookie
    return fetch(url, options);
  }

  /* ── Показываем сообщение об ошибке орфографии ── */
  function spellMsg(errors) {
    if (!errors || !errors.length) return;
    var words = errors.slice(0, 4).join(', ');
    var more  = errors.length > 4 ? (' и ещё ' + (errors.length - 4)) : '';
    afMsg('Возможные ошибки: ' + words + more);
  }

  /* ═══════════════════════════════════════════
     ГЕРОИ ВОЙНЫ
  ═══════════════════════════════════════════ */

  window.afSaveHero = function () {
    var name = document.getElementById('ah-name').value.trim();
    var bio  = document.getElementById('ah-bio').value.trim();
    if (!name || !bio) {
      afMsg('Заполните обязательные поля (имя и биография)');
      return;
    }

    /* Конвертируем фото в base64 через оригинальную функцию */
    afToBase64('ah-photo', function (src) {
      var payload = {
        name:  name,
        rank:  document.getElementById('ah-rank').value.trim(),
        years: document.getElementById('ah-years').value.trim(),
        unit:  document.getElementById('ah-unit').value.trim(),
        award: document.getElementById('ah-award').value.trim(),
        bio:   bio,
        src:   src || ''
      };

      apiFetch('/api/heroes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
        .then(function (r) { return r.json(); })
        .then(function (h) {
          if (h.error) { afMsg('Ошибка: ' + h.error); return; }
          afRenderHero(h);
          afClose('af-heroes');
          afResetForm(['ah-photo', 'ah-name', 'ah-rank', 'ah-years', 'ah-unit', 'ah-award', 'ah-bio']);
          var prev = document.getElementById('ah-prev');
          if (prev) prev.style.display = 'none';
          afMsg('Герой добавлен! Ожидает проверки администратором.');
          spellMsg(h.spell_errors);
        })
        .catch(function (e) { afMsg('Ошибка отправки: ' + e.message); });
    });
  };

  /* ═══════════════════════════════════════════
     ФОТО-ХРОНИКА
  ═══════════════════════════════════════════ */

  window.afSaveKhronika = function () {
    var title = document.getElementById('ak-title').value.trim();
    var bio   = document.getElementById('ak-bio').value.trim();
    if (!title || !bio) {
      afMsg('Заполните обязательные поля (подпись и история)');
      return;
    }
    var section = document.getElementById('ak-section').value;

    afToBase64('ak-photo', function (src) {
      if (!src) { afMsg('Добавьте фотографию'); return; }

      apiFetch('/api/khronika/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title, bio: bio, section: section, src: src })
      })
        .then(function (r) { return r.json(); })
        .then(function (item) {
          if (item.error) { afMsg('Ошибка: ' + item.error); return; }
          afRenderKhronika(item);
          afClose('af-khronika');
          afResetForm(['ak-photo', 'ak-title', 'ak-bio']);
          var prev = document.getElementById('ak-prev');
          if (prev) prev.style.display = 'none';
          afMsg('Фото добавлено! Ожидает проверки администратором.');
          spellMsg(item.spell_errors);
        })
        .catch(function (e) { afMsg('Ошибка: ' + e.message); });
    });
  };

  /* ═══════════════════════════════════════════
     ПИСЬМА С ФРОНТА
  ═══════════════════════════════════════════ */

  window.afSaveLetter = function () {
    var sender = document.getElementById('al-sender').value.trim();
    var text   = document.getElementById('al-text').value.trim();
    if (!sender || !text) {
      afMsg('Заполните обязательные поля (автор и текст)');
      return;
    }

    apiFetch('/api/letters/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        year:   document.getElementById('al-year').value.trim(),
        sender: sender,
        to:     document.getElementById('al-to').value.trim(),
        text:   text
      })
    })
      .then(function (r) { return r.json(); })
      .then(function (lt) {
        if (lt.error) { afMsg('Ошибка: ' + lt.error); return; }
        afRenderLetter(lt);
        afClose('af-letters');
        afResetForm(['al-sender', 'al-year', 'al-to', 'al-text']);
        afMsg('Письмо добавлено! Ожидает проверки администратором.');
        spellMsg(lt.spell_errors);
      })
      .catch(function (e) { afMsg('Ошибка: ' + e.message); });
  };

  /* ═══════════════════════════════════════════
     УДАЛЕНИЕ КАРТОЧЕК
  ═══════════════════════════════════════════ */

  window.afDelCard = function (uid, storageKey, cardEl) {
    if (!confirm('Удалить запись?')) return;

    /* Определяем эндпоинт по ключу хранилища */
    var endpoint;
    if      (storageKey === 'user_heroes')   endpoint = '/api/heroes/'   + uid + '/';
    else if (storageKey === 'user_khronika') endpoint = '/api/khronika/' + uid + '/';
    else if (storageKey === 'user_letters')  endpoint = '/api/letters/'  + uid + '/';
    else {
      afMsg('Неизвестный тип записи');
      return;
    }

    apiFetch(endpoint, { method: 'DELETE' })
      .then(function (r) {
        if (r.ok) {
          if (cardEl) cardEl.remove();
          afMsg('Удалено');
        } else {
          r.json().then(function (d) { afMsg('Ошибка: ' + (d.error || r.status)); });
        }
      })
      .catch(function (e) { afMsg('Ошибка сети: ' + e.message); });
  };

  /* ═══════════════════════════════════════════
     ЗАГРУЗКА ДАННЫХ ПРИ ОТКРЫТИИ СТРАНИЦЫ
  ═══════════════════════════════════════════ */

  document.addEventListener('DOMContentLoaded', function () {
    /* Очищаем старые данные localStorage, чтобы не было дублей */
    try {
      localStorage.removeItem('user_heroes');
      localStorage.removeItem('user_khronika');
      localStorage.removeItem('user_letters');
    } catch (e) { /* ignore */ }

    /* Загружаем одобренные + свои записи из БД */
    fetch('/api/heroes/', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (items) { items.forEach(afRenderHero); })
      .catch(function () { /* сеть недоступна — ничего не рисуем */ });

    fetch('/api/khronika/', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (items) { items.forEach(afRenderKhronika); })
      .catch(function () {});

    fetch('/api/letters/', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (items) { items.forEach(afRenderLetter); })
      .catch(function () {});
  });

})();
