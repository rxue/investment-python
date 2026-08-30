# Python
## `uv`
### Video tutorial: https://www.youtube.com/watch?v=AMdG7IjgSPM
#### Problem of using `venv`: https://www.youtube.com/watch?v=AMdG7IjgSPM&t=289s
multiple steps of the developer continuing the existing project:
* create and activate one's own virtual environment
* install the dependencies from `requirement.txt` fiels

#### [`uv init`](https://www.youtube.com/watch?v=AMdG7IjgSPM&t=351s) to initialize an existing project
#### [project types](https://www.youtube.com/watch?v=AMdG7IjgSPM&t=374s) to choose from in `uv`
* *default* type `--app` : simple project structure for application, scripts and web servers etc.
* `--lib`
#### [project structure created by `uv init` command](https://www.youtube.com/watch?v=AMdG7IjgSPM&t=419s)
##### [.python-version](https://www.youtube.com/watch?v=AMdG7IjgSPM&t=450s)
##### [`pyproject.toml`](https://www.youtube.com/watch?v=AMdG7IjgSPM&t=506s)
* [`uv add`](https://www.youtube.com/watch?v=AMdG7IjgSPM&t=544s)
`uv add` automatically create *virtual environment* with `venv`
## `Mypy`
### Tutorial: https://www.youtube.com/watch?v=Y9fT4HVdCuQ
## Fluent Python
### Part II Functions as Objects
#### Chapter 9: Decorators and Closures
##### Decorators in the Standard Library
###### Memoization with `functools.cache`
## IDE: PyCharm
EAP - *Early Access Program*

# DevOps
## `cron` in Linux
revision: the `*` marked in the hour/min/day etc. means every. For instance, `cron: "0 22 * * 1-5"`, where the first `*` is every day of month, the second `*` is every month. When changing the first `0` to `*`, i.e. the whole cron script to `cron: "* 22 * * 1-5"`, the first star makes the scheduled program executed every minute
## Github CLI - `gh`
### `gh workflow run price_tracker.yml` to trigger the event

# Domain Knowledge
## *Index*
A type of statistic with no natural units of measurement; for example, *correlation*
