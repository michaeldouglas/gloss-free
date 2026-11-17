from __future__ import annotations
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from libras_translation.metadata_validation import validate_dataset, normalize_filename_key
from libras_translation.vlibrasil_validation import generate_vlibrasil_artifacts
from libras_translation.vlibrasil_publication import publish_generation, finalize_vlibrasil, digest, canonical_inventory

FIELDS = ["video_id","video_name","class","user_id","width","height","fps","url_page","url_download"]
def table(path, rows):
    with path.open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
def record(name, class_name):
    return dict(video_id="id-"+name,video_name=name,**{"class":class_name},user_id="Articulador1",width="160",height="120",fps="50",url_page="https://example.org/sign",url_download="https://example.org/video.mp4")
def probe(path):
    return dict(status="ok",video_stream_count=1,actual_width=160,actual_height=120,actual_fps=25.0,
                actual_frame_count=50,actual_duration_seconds=2.0,codec="h264",
                actual_fps_source="avg_frame_rate",actual_frame_count_source="nb_frames",
                field_status={key:"available" for key in ("width","height","fps","frame_count","duration","codec")})
def tool(*args,**kwargs):
    return type("Completed",(),dict(returncode=0,stdout="fixture version",stderr=""))()

class VCloseoutTests(unittest.TestCase):
    def fixture(self, root, *, duplicate=False):
        dataset=root/"v-librasil-raw"
        (dataset/"videos").mkdir(parents=True)
        names=[(r"Frente\Á Frente_Articulador1.mp4","Frente\uf05cÁ Frente_Articulador1.mp4",r"Frente\Á Frente"),
               ('Cérebro (de "ervilha")_Articulador1.mp4',"Cérebro (de \uf022ervilha\uf022)_Articulador1.mp4",'Cérebro (de "ervilha")'),
               ("O quê?_Articulador1.mp4","O quê\uf03f_Articulador1.mp4","O quê?")]
        rows=[]
        for name,physical,cls in names:
            (dataset/"videos"/physical).write_bytes(b"fixture")
            rows.append(record(name,cls))
        if duplicate:
            rows.append({**rows[0],"video_name":" "+rows[0]["video_name"].upper()+" "})
        table(dataset/"annotations.csv",rows)
        exceptions=[]
        for name in ("Congelar_Articulador3.mp4","Criança_Articulador3.mp4","Poesia_Articulador2.mp4"):
            row=record(name,name.rsplit("_",1)[0]);row.update(width="0",height="0",fps="0",user_id=name.rsplit("_",1)[1][:-4])
            exceptions.append(row)
        table(dataset/"error.csv",exceptions)
        payload=validate_dataset(dataset/"annotations.csv",dataset/"videos",root/"technical",
                                 dataset="v-librasil-raw",probe_function=probe,tool_runner=tool)
        return dataset,payload
    def test_literal_pua_names_and_exceptions_are_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dataset,payload=self.fixture(root)
            result=generate_vlibrasil_artifacts(dataset_root=dataset,metadata_payload=payload,output_root=root/"quality")
            self.assertEqual(result["summary"]["key_reconciliation"]["matched"],3)
            self.assertEqual(len(result["manifest_rows"]),3)
            self.assertTrue(all(row["dataset_valid"] for row in result["manifest_rows"]))
            self.assertEqual(result["summary"]["counts"]["by_severity"],dict(CRITICAL=0,ERROR=0,WARNING=0,INFO=3))
            self.assertEqual(result["summary"]["counts"]["affected_files"],0)
            self.assertEqual(result["summary"]["counts"]["unreadable_files"],0)
            self.assertIn("\\",result["manifest_rows"][0]["filesystem_key"])
    def test_collision_does_not_choose_a_matching_annotation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dataset,payload=self.fixture(root,duplicate=True)
            result=generate_vlibrasil_artifacts(dataset_root=dataset,metadata_payload=payload,output_root=root/"quality")
            collided=[row for row in result["manifest_rows"] if normalize_filename_key(row["video_name"]).startswith("frente")]
            self.assertEqual(len(collided),2)
            self.assertTrue(all(row["metadata_match"]=="duplicate" and not row["dataset_valid"] for row in collided))
            self.assertEqual(result["summary"]["key_reconciliation"]["normalized_duplicate_annotations"],1)
    def test_metadata_mismatch_is_not_physical_unreadability(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dataset,payload=self.fixture(root)
            payload["results"][0]["comparison"]["width_status"]="mismatch"
            payload["results"][0]["comparison"]["overall_status"]="mismatch"
            result=generate_vlibrasil_artifacts(dataset_root=dataset,metadata_payload=payload,output_root=root/"quality")
            mismatch=[row for row in result["manifest_rows"] if row["metadata_match"]=="mismatch"]
            self.assertEqual(len(mismatch),1)
            self.assertTrue(mismatch[0]["technical_valid"])
            self.assertFalse(mismatch[0]["dataset_valid"])
    def test_inventory_timestamp_precision_does_not_create_false_source_changes(self):
        before=[dict(relative_path="videos/a.mp4",size_bytes=1,last_write_utc="2026-10-04T00:46:43.708125Z")]
        after=[dict(relative_path="videos/a.mp4",size_bytes=1,last_write_utc="2026-10-04T00:46:43.7081250Z")]
        self.assertEqual(canonical_inventory(before),canonical_inventory(after))
        after[0]["last_write_utc"]="2026-10-04T00:46:43.7081251Z"
        self.assertNotEqual(canonical_inventory(before),canonical_inventory(after))

    def test_prepared_generation_is_validated_and_published_as_one_set(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);dataset,payload=self.fixture(root/"inputs")
            prepared=root/"inputs/technical"
            inventory=[dict(relative_path=path.relative_to(dataset).as_posix(),size_bytes=path.stat().st_size,last_write_ns=path.stat().st_mtime_ns) for path in sorted((dataset/"videos").rglob("*")) if path.is_file()]
            source=dict(annotations_sha256=digest(dataset/"annotations.csv"),error_sha256=digest(dataset/"error.csv"),inventory=inventory)
            for phase in ("before","after"):
                (prepared/("source_integrity."+phase+".json")).write_text(json.dumps({"snapshot_data":source} if phase=="after" else source),encoding="utf-8")
            closed=finalize_vlibrasil(dataset,root/"outputs",prepared_metadata=prepared)
            canonical=closed["canonical"]
            publication=json.loads((canonical/"publication.json").read_text(encoding="utf-8"))
            self.assertEqual(publication["state"],"complete")
            self.assertEqual(publication["manifest_rows"],3)
            for relative,sha in publication["artifacts_sha256"].items():
                self.assertEqual(digest(canonical/relative),sha,relative)
            summary=json.loads((canonical/"reports/metadata_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["review_status"],"pending_human_review")
            self.assertEqual(summary["stage1_review"]["requirements"][0]["status"],"PASS")
            for csv_name in ("metadata_comparison.csv","video_metadata.csv"):
                with (canonical/csv_name).open(encoding="utf-8",newline="") as stream:
                    self.assertTrue(all(row["metadata_match"]=="match" for row in csv.DictReader(stream)))
            technical=json.loads((canonical/"metadata_validation.json").read_text(encoding="utf-8"))
            self.assertEqual(technical["run"]["input_csv"],"data/raw/v-librasil-raw/annotations.csv")
            self.assertIsNone(publication["global_stage1_decision"])

    def test_failed_directory_promotion_restores_previous_canonical(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);canonical=root/"v-librasil-raw";canonical.mkdir()
            (canonical/"old").write_text("preserved")
            stage=root/".v-librasil-fixture";stage.mkdir();(stage/"new").write_text("new")
            registry=root/"validation_runs.json";registry.write_text('{"runs":{"minds-libras-raw":{"decision":"GO"}}}')
            before=registry.read_bytes()
            import libras_translation.vlibrasil_publication as pub
            original=pub.os.replace
            def fail(source,target):
                if Path(source)==stage: raise OSError("fixture promotion failure")
                return original(source,target)
            with patch.object(pub.os,"replace",side_effect=fail),self.assertRaises(OSError):
                publish_generation(stage,root,dict(decision="GO",generated_at_utc="fixture"),generation_id="fixture")
            self.assertEqual((canonical/"old").read_text(),"preserved")
            self.assertFalse((canonical/"new").exists())
            self.assertEqual(registry.read_bytes(),before)
            self.assertFalse((root/".v-librasil-publication.lock").exists())
    def test_success_moves_legacy_and_preserves_minds_registry(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/"v-librasil-raw").mkdir();(root/"v-librasil-raw/old").write_text("old")
            stage=root/".v-librasil-fixture";stage.mkdir();(stage/"metadata_validation.json").write_text("{}")
            (root/"reports").mkdir();(root/"reports/metadata_summary.json").write_text('{"dataset":"v-librasil-raw"}')
            (root/"reports/metadata_issues.csv").write_text("old issues")
            minds=dict(decision="GO",path="unchanged")
            (root/"validation_runs.json").write_text(json.dumps(dict(runs={"minds-libras-raw":minds})))
            published=publish_generation(stage,root,dict(decision="GO",generated_at_utc="fixture"),generation_id="fixture")
            self.assertTrue((published/"metadata_validation.json").exists())
            self.assertFalse((root/"reports/metadata_summary.json").exists())
            self.assertTrue((root/"superseded/v-librasil-fixture/legacy-root/reports/metadata_summary.json").exists())
            self.assertEqual(json.loads((root/"validation_runs.json").read_text())["runs"]["minds-libras-raw"],minds)

if __name__=="__main__":
    unittest.main()
