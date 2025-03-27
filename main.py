import configparser
import os
import glob
import log
import fitz
import argparse
from dvelopdmspy.dvelopdmspy import DvelopDmsPy, DvelopDMSPyException


current_dir = os.path.abspath(os.path.dirname(__file__))
config = configparser.ConfigParser(delimiters=('=',), interpolation=None)
configpath = os.path.join(current_dir, 'config.ini')
config.read(configpath, encoding='utf-8')

logger = log.setup_custom_logger('root', config.get('Logging', 'method', fallback='file'),
                                 config.get('Logging', 'level', fallback='info'),
                                 graylog_host=config.get('Logging', 'graylog_host', fallback=None),
                                 graylog_port=config.getint('Logging', 'graylog_port', fallback=0))


def get_pdf_page_count(pdf_path):
    doc_pdf = fitz.open(pdf_path)
    return len(doc_pdf)


def delete_temp_files(temp_path: str):
    if os.path.exists(temp_path):
        for file in glob.glob(os.path.join(temp_path, "*")):
            if os.path.basename(file) != ".gitignore":
                try:
                    os.remove(file)
                except Exception as ex:
                    print(f"Fehler beim Löschen von {file}: {ex}")
    else:
        print(f"Ordner '{temp_path}' nicht gefunden.")


def get_file_info(filepath: str) -> dict | None:
    try:
        page_count = get_pdf_page_count(filepath)
        return {
            'page_count': page_count
        }
    except Exception as ex:
        logger.error(f"Exception in dms_butler.get_file_info: {str(ex)}")
        return None


def process_profile(profile_config: dict, profile_name: str, dms: DvelopDmsPy, temp_folder: str, whatif: bool = False,
                    verbose: bool = False):
    if whatif:
        logger.info(f"Profile {profile_name}: PING")
    print(f"Profile: {profile_name}")
    allowed_filetypes_raw = profile_config.get("allowed_filetypes")
    cats_raw = profile_config.get("categories").split("|") if profile_config.get("categories") else None
    fulltext = profile_config.get("fulltext")
    min_pages = int(profile_config.get("min_pages"))
    max_pages = int(profile_config.get("max_pages"))
    props_raw = profile_config.get("search_props")
    set_props_raw = profile_config.get("set_props")
    set_props_pairs_raw = set_props_raw.split("|")
    allowed_filetypes = allowed_filetypes_raw.lower().split("|")
    prop_pairs_raw = props_raw.split("|")
    searchprops = {}
    for prop_pair in prop_pairs_raw:
        prop_parts = prop_pair.split(":")
        prop_key = prop_parts[0]
        prop_value = prop_parts[1]
        dms.add_property(display_name=prop_key, pvalue=prop_value, pdict=searchprops)
    print(f"Search props: {searchprops}")
    setprops = []
    for set_prop_pair in set_props_pairs_raw:
        prop_parts = set_prop_pair.split(":")
        prop_key = prop_parts[0]
        prop_value = prop_parts[1]
        dms.add_upload_property(display_name=prop_key, pvalue=prop_value, plist=setprops)
    print(f"Set Props: {setprops}")
    cats = []
    for cat in cats_raw:
        cats = dms.add_category(cat, cats)

    docs = dms.get_documents(categories=cats, fulltext=fulltext, properties=searchprops)
    print(f"Matched raw doc count: {len(docs)}")
    if whatif and not verbose:
        return
    doc_count = 0
    ch_count = 0
    for doc in docs:
        if doc.filetype.lower() not in allowed_filetypes:
            continue
        file_path = os.path.join(temp_folder, f"{doc.id_}.{doc.filetype.lower()}")
        if not os.path.exists(file_path):
            try:
                dms.download_doc_blob(doc_id=doc.id_, dest_file=file_path)
            except DvelopDMSPyException as e:
                logger.error(f"Dvelop Exception while downloading file {doc.id_}: {str(e)}")
                continue
        pdf_info = get_file_info(filepath=file_path)
        if not pdf_info:
            print(f"No Info for file {doc.id_}")
            continue
        if pdf_info["page_count"] > max_pages or pdf_info["page_count"] < min_pages:
            logger.debug(f"Ignored {doc.id_} because of page count mismatch. "
                         f"{min_pages} > {pdf_info['page_count']} > {max_pages}")
            continue
        doc_count += 1
        if whatif and verbose:
            print(f"doc {doc.id_}: {doc.caption} ({pdf_info['page_count']} pages)")
        if whatif:
            continue
        dms.update_properties(doc_id=doc.id_, properties=setprops,
                              alteration_msg=profile_config.get("alt_message", "Changed by dms_butler"),
                              state_change=False)
        ch_count += 1
        logger.info(f"Changed doc {doc.id_} with profile {profile_name}")
        print(f"Changed doc {doc.id_} ({ch_count} / {len(docs)})")
    print(f"Matched doc count: {doc_count}")


def main():
    parser = argparse.ArgumentParser(description="Manipulate dms properties with rules")
    parser.add_argument("--whatif", action="store_true", help="Display affected doc count")
    parser.add_argument("--verbose", action="store_true", help="Display affected doc details (only valid"
                                                               " in combination with whatif")
    args = parser.parse_args()
    if args.whatif:
        print("Simulation activated")
    if args.verbose:
        print("Verbose mode activated")
    profiles = configparser.ConfigParser(delimiters=('=',), interpolation=None)
    profilepath = os.path.join(current_dir, 'profiles.ini')
    profiles.read(profilepath, encoding='utf-8')
    tfolder = os.path.join(current_dir, "temp")

    tdms = DvelopDmsPy(hostname=config.get("DMS", "host"),
                       api_key=config.get("DMS", "api_key"),
                       repository=config.get("DMS", "repo"))

    for profile_entry in profiles.sections():
        process_profile(dict(profiles[profile_entry]), profile_name=profile_entry, dms=tdms, temp_folder=tfolder,
                        whatif=args.whatif, verbose=args.verbose)


if __name__ == "__main__":
    main()
