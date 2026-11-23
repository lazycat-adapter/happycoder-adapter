import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class AdapterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.action = yaml.safe_load((ROOT / "lazycat-action.yml").read_text())
        cls.manifest = yaml.safe_load((ROOT / "lzc-manifest.yml").read_text())
        cls.package = yaml.safe_load((ROOT / "package.yml").read_text())
        cls.dockerfile = (ROOT / "image" / "Dockerfile").read_text()

    def test_package_identity_and_initial_patch_version(self):
        self.assertEqual(self.package["package"], "cloud.lazycat.app.happycoder")
        self.assertEqual(self.package["version"], "1.5.0")
        self.assertEqual(self.package["homepage"], "https://github.com/slopus/happy")

    def test_source_selects_only_stable_happy_app_tags(self):
        source = self.action["source"]
        self.assertEqual(source["kind"], "git")
        self.assertEqual(source["url"], "https://github.com/slopus/happy.git")
        self.assertEqual(source["select"]["strategy"], "semver-tag")
        self.assertEqual(source["select"]["tag_regex"], r"^v[0-9]+\.[0-9]+\.[0-9]+$")

    def test_single_prepared_image_is_persisted_and_exposed_on_both_domains(self):
        application = self.manifest["application"]
        self.assertEqual(application["subdomain"], "happyweb")
        self.assertEqual(application["secondary_domains"], ["happyserver"])
        self.assertEqual(application["routes"], ["/=http://app.cloud.lazycat.app.happycoder.lzcapp:80"])
        self.assertEqual(self.manifest["services"]["app"]["binds"], ["/lzcapp/var/data:/data"])

    def test_build_combines_web_and_server_and_rewrites_lazycat_domain(self):
        self.assertIn("EXPO_PUBLIC_HAPPY_SERVER_URL=https://happyserver.__LAZYCAT_BOX_DOMAIN__", self.dockerfile)
        self.assertIn("packages/happy-app/dist", self.dockerfile)
        self.assertIn("packages/happy-server/sources/standalone.ts", self.dockerfile)
        self.assertIn("happyserver.${LAZYCAT_BOX_DOMAIN}", self.dockerfile)

    def test_prepare_script_builds_the_combined_image_from_selected_source(self):
        prepare = (ROOT / "image" / "prepare.py").read_text()
        self.assertIn("LAZYCAT_SOURCE_DIR", prepare)
        self.assertIn("LAZYCAT_OUTPUT_IMAGE", prepare)
        self.assertIn("docker", prepare)


if __name__ == "__main__":
    unittest.main()
