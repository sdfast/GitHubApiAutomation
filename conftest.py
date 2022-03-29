import pytest

from utils.utilities import get_config, delete_file


@pytest.fixture()
def context() -> dict:
    return get_config("config.yaml")


def pytest_bdd_after_scenario(request):
    context = request.getfixturevalue('context')

    delete_response = context["BasicAuth"].session.delete(
        url="https://api.github.com/repos/" + context["github_user"] + "/" + context[
            "repo_name"])

    delete_file(context['commit_file_path'])
    assert delete_response.status_code == 204


def pytest_runtest_teardown(item):
    print(f"Tearing down {item}")
