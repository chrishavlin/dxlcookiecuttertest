#!/usr/bin/env python
import os
import yaml
from shutil import copyfile, rmtree
from collections import defaultdict
PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)


def remove_file(filepath):
    os.remove(get_project_filepath(filepath))


def get_project_filepath(filepath):
    return os.path.join(PROJECT_DIRECTORY, filepath)


def _parse_package(version_string):
    for op in [">=", "==", "<=", "<", ">"]:
        if op in version_string:
            package = version_string.split(op)[0]
            return package
    # no version pin in version_string, just return it
    return version_string


def _check_reqs_for_duplicates(all_reqs):
    packages = []
    duplicates = []

    # first get the list of duplicated packages
    for req in all_reqs:
        package = _parse_package(req)
        if package in packages:
            duplicates.append(package)
            print("Warning: duplicate requirement found, check requirements.txt "
                  "in your new package directory")
        packages.append(package)

    # if there are duplicates, copy over reqs but flag the duplicates
    if duplicates:
        reqs = []
        for req in all_reqs:
            if _parse_package(req) in duplicates:
                reqs.append(req + " <<< duplicate")
            else:
                reqs.append(req)
        return reqs
    return all_reqs


def _generate_requirements():

    # generates the requirements.txt file.

    # the following dict defines the string to check against the cookiecutter
    # value
    req_set_truth = defaultdict(lambda: "y")
    req_set_truth['click'] = 'click'

    # the read in the yaml containing the requirement sets
    reqfi = "requirement_sets.yml"
    with open(reqfi) as f:
        req_yaml = yaml.load(f.read(), Loader=yaml.FullLoader)
    req_filename = "requirements.txt"  # the final requirements file

    # generate the list of requirements
    all_reqs = []
    if '{{ cookiecutter.command_line_interface|lower }}' == req_set_truth["click"]:
        all_reqs += req_yaml["click"]
    if '{{ cookiecutter.include_yt_requirements|lower }}' == req_set_truth["yt"][0]:
        all_reqs += req_yaml["yt"]

    all_reqs = _check_reqs_for_duplicates(all_reqs)

    # write out the requirements
    with open(req_filename, "w") as reqs:
        reqs.write("\n".join(all_reqs))

    # delete the yaml file from the new package files
    remove_file(reqfi)


def copy_frontend_template(dest_dir, template_dir, fe_type):

    source_dir = os.path.join(template_dir, fe_type)
    init_contents = None
    for fi in os.listdir(source_dir):
        if fi == "__init__.py":
            with open(os.path.join(source_dir, fi), "r") as fhandle:
                init_contents = "\n" + fhandle.read() + "\n"
        else:
            copyfile(os.path.join(source_dir, fi),
                     os.path.join(dest_dir, fi))
    return init_contents


def _select_frontend(project_dir):
    # frontend selection: copies over files from frontend_templates, merges
    # the __init__.py file and deletes the frontend_templates directory

    fe_type = '{{ cookiecutter.frontend_type }}'.lower()
    template_dir = os.path.join(project_dir, "frontend_templates")
    if fe_type == "amr skeleton":
        init_contents = copy_frontend_template(project_dir, template_dir, "skeleton")
    elif "stream" in fe_type:
        init_contents = copy_frontend_template(project_dir, template_dir, "stream")

    if init_contents is not None:
        with open(os.path.join(project_dir, "__init__.py"), "a") as fhandle:
            fhandle.write(init_contents)

    rmtree(template_dir)


if __name__ == '__main__':

    project_dir = '{{ cookiecutter.project_slug }}'

    if '{{ cookiecutter.create_author_file }}' != 'y':
        remove_file('AUTHORS.rst')
        remove_file('docs/authors.rst')

    if 'no' in '{{ cookiecutter.command_line_interface|lower }}':
        cli_file = os.path.join(project_dir, 'cli.py')
        remove_file(cli_file)

    if 'Not open source' == '{{ cookiecutter.open_source_license }}':
        remove_file('LICENSE')

    _generate_requirements()
    _select_frontend(project_dir)

