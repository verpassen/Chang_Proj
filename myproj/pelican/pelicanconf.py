#!/usr/bin/env python
# -*- coding: utf-8 -*- #

AUTHOR = 'Brent chang'
SITENAME = 'It\'s my BLOG'
SITESUBTITLE = 'Write something down'
SITEURL = ''

PATH = 'content/pages'
ARTICLE_PATH= []
ARICLE_URL = '{date:%Y}/{}'

TIMEZONE = 'Asia/Taipei'
DEFAULT_LANG = 'en'

THEME = 'themes/clean'
GITHUB_URL = 'github.com/verpassen'


# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Pelican', 'https://getpelican.com/'),
         ('Hexo', 'https://verpassen.github.io'),
         ('Jinja2', 'https://palletsprojects.com/p/jinja/'),
         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('github', 'https://github.com/verpassen'),
          ('Linkedin', 'https://linkedin.com/in/brent-chang-71318ba8/'),)

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
