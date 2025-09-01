use std::{env, path::PathBuf};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // tonic_prost_build::compile_protos("proto/queue_service.proto")?;
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());
    tonic_prost_build::configure()
        .file_descriptor_set_path(out_dir.join("queue_descriptor.bin"))
        .type_attribute(".", "#[derive(serde::Serialize,serde::Deserialize)]")
        .compile_protos(&["../proto/queue_service.proto"], &["../proto"])
        .unwrap();
    Ok(())
}
