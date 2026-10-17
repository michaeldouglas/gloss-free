interface AvatarFilePickerProps {
  disabled?: boolean;
  onSelect: (file: File) => void;
}

export function AvatarFilePicker({ disabled = false, onSelect }: AvatarFilePickerProps) {
  return (
    <label className={`file-picker${disabled ? " file-picker--disabled" : ""}`}>
      <span>Carregar avatar</span>
      <small>VRM 1.0, GLB ou GLTF</small>
      <input
        type="file"
        accept=".vrm,.glb,.gltf,model/gltf-binary,model/gltf+json"
        disabled={disabled}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onSelect(file);
          event.target.value = "";
        }}
      />
    </label>
  );
}
