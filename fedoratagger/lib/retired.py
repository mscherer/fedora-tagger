"""
Tagger need to remove the packages in retired status.
Is that the script Should be run as:

FEDORATAGGER_CONFIG = /etc/fedora-tagger/fedora-tagger.cfg python /path/to/fedoratagger/lib/retired.py
"""
import requests

import model as m
import fedoratagger as ft

import logging

log = logging.getLogger("fedoratagger-remove")
log.setLevel(logging.DEBUG)
logging.basicConfig()

PDC_URL = 'https://pdc.fedoraproject.org/rest_api/v1/component-branches'


def get_retired_packages():

    packages = []

    args = {
        'name': 'f28',
        'active': False,
    }

    response = requests.get(PDC_URL, args)
    if response.ok:
        output = response.json()
    else:
        response.raise_for_status()
    for pkg in output['results']:
        pkg_name = pkg['global_component']
        packages.append(pkg_name)
    pdc_api_url = output['next']

    while pdc_api_url:
        response = requests.get(pdc_api_url)
        if response.ok:
            output = response.json()
        else:
            response.raise_for_status()
        for pkg in output['results']:
            pkg_name = pkg['global_component']
            packages.append(pkg_name)

        pdc_api_url = output['next']

    return packages


def del_packages():

    log.info('Deleting packages.')

    s = 0
    e = 100
    pkgs = get_retired_packages()
    l = len(pkgs)
    while (pkgs[s:e]):
        log.info('searching packages [%i] to [%i] of [%i]' % (s, e, l))
        package = ft.SESSION.query(
            m.Package).filter(
            m.Package.name.in_(pkgs[s:e]))
        s = e
        e = e + 100

        for r in package:
            tag = ft.SESSION.query(m.Tag).filter(m.Tag.package_id == r.id)
            usage = ft.SESSION.query(m.Usage).filter(m.Usage.package_id == r.id)
            rating = ft.SESSION.query(
                m.Rating).filter(
                m.Rating.package_id == r.id)
            for t in tag:
                vote = ft.SESSION.query(m.Vote).filter(m.Vote.tag_id == t.id)
                vote.delete()
            tag.delete()
            usage.delete()
            rating.delete()
        package.delete(synchronize_session='fetch')

        ft.SESSION.commit()


def main():

    del_packages()


if __name__ == '__main__':
    main()
