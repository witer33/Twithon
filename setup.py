from distutils.core import setup
setup(
  name = 'twithon',
  packages = ['twithon'],
  version = '0.0.3.2',
  license='MIT',
  description = 'A python wrapper over Twitch API to build bots and applications.',
  author = 'Witer33',
  author_email = 'dev@witer33.com',
  url = 'https://github.com/witer33/Twithon',
  download_url = 'https://github.com/witer33/Twithon/archive/v_0.0.3.2.tar.gz',
  keywords = ['Twitch', 'chatbot', 'IRC'],
  install_requires=["requests"],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
)
