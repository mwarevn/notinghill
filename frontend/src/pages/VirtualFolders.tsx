// NotingHill — pages/VirtualFolders.tsx
import { useEffect, useState, useCallback } from 'react'
import { useStore } from '../store'
import {
  listVFolders, createVFolder, updateVFolder, deleteVFolder,
  getVFolderItems, removeItemFromVFolder, openFile, revealFile,
} from '../api/client'
import { SectionHeader, EmptyState, Badge } from '../components/ui'
import { formatSize, formatDate } from '../utils/helpers'

// ── Types ────────────────────────────────────────────────────
interface VFolder {
  vf_id: number
  parent_vf_id: number | null
  name: string
  color: string
  icon: string
  item_count: number
}

// ── Tree builder ─────────────────────────────────────────────
function buildTree(folders: VFolder[]): (VFolder & { children: any[] })[] {
  const map = new Map<number, any>()
  folders.forEach(f => map.set(f.vf_id, { ...f, children: [] }))
  const roots: any[] = []
  map.forEach(node => {
    if (node.parent_vf_id && map.has(node.parent_vf_id)) {
      map.get(node.parent_vf_id).children.push(node)
    } else {
      roots.push(node)
    }
  })
  return roots
}

// ── FolderNode ───────────────────────────────────────────────
function FolderNode({
  node, depth, selectedId, onSelect, onCreateChild, onRename, onDelete,
}: {
  node: any; depth: number; selectedId: number | null
  onSelect: (id: number) => void
  onCreateChild: (parentId: number) => void
  onRename: (node: any) => void
  onDelete: (node: any) => void
}) {
  const [expanded, setExpanded] = useState(true)
  const selected = selectedId === node.vf_id
  const hasChildren = node.children.length > 0

  return (
    <div>
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '6px 10px',
          paddingLeft: 10 + depth * 16,
          cursor: 'pointer',
          background: selected ? 'rgba(103,232,249,0.10)' : 'transparent',
          borderLeft: selected ? `2px solid ${node.color}` : '2px solid transparent',
          borderRadius: 8,
          marginBottom: 2,
        }}
        onClick={() => onSelect(node.vf_id)}
      >
        {hasChildren ? (
          <span
            style={{ fontSize: 9, color: 'var(--text3)', width: 12, flexShrink: 0 }}
            onClick={e => { e.stopPropagation(); setExpanded(!expanded) }}
          >
            {expanded ? '▾' : '▸'}
          </span>
        ) : (
          <span style={{ width: 12, flexShrink: 0 }} />
        )}

        <span style={{ fontSize: 14, lineHeight: 1 }}>{node.icon}</span>
        <span style={{
          flex: 1, fontSize: 11, color: selected ? node.color : 'var(--text)',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {node.name}
        </span>
        <span style={{ fontSize: 9, color: 'var(--text3)', flexShrink: 0 }}>
          {node.item_count}
        </span>

        <div style={{ display: 'flex', gap: 4, flexShrink: 0 }} onClick={e => e.stopPropagation()}>
          <button
            className="nh-btn"
            style={{ padding: '2px 6px', fontSize: 9, borderRadius: 6 }}
            title="Add subfolder"
            onClick={() => onCreateChild(node.vf_id)}
          >+</button>
          <button
            className="nh-btn"
            style={{ padding: '2px 6px', fontSize: 9, borderRadius: 6 }}
            title="Rename"
            onClick={() => onRename(node)}
          >✎</button>
          <button
            className="nh-btn danger"
            style={{ padding: '2px 6px', fontSize: 9, borderRadius: 6 }}
            title="Delete"
            onClick={() => onDelete(node)}
          >✕</button>
        </div>
      </div>

      {expanded && hasChildren && (
        <div>
          {node.children.map((child: any) => (
            <FolderNode
              key={child.vf_id}
              node={child}
              depth={depth + 1}
              selectedId={selectedId}
              onSelect={onSelect}
              onCreateChild={onCreateChild}
              onRename={onRename}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ── Modal ────────────────────────────────────────────────────
const ICONS = ['📁', '⭐', '🏠', '💼', '🎵', '📸', '📄', '🎬', '🗂', '🔖', '💡', '🔒']
const COLORS = ['#67e8f9', '#a78bfa', '#fbbf24', '#22c55e', '#fb7185', '#f472b6', '#38bdf8', '#fb923c']

function FolderModal({
  mode, initial, parentId, allFolders, onSave, onClose,
}: {
  mode: 'create' | 'edit'
  initial?: any
  parentId?: number | null
  allFolders: VFolder[]
  onSave: (data: any) => void
  onClose: () => void
}) {
  const [name, setName] = useState(initial?.name ?? '')
  const [color, setColor] = useState(initial?.color ?? '#67e8f9')
  const [icon, setIcon] = useState(initial?.icon ?? '📁')
  const [parentVfId, setParentVfId] = useState<number | null>(
    initial?.parent_vf_id ?? parentId ?? null
  )

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(4,10,16,0.85)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1400,
    }} onClick={onClose}>
      <div style={{
        background: 'var(--bg1)', border: '1px solid var(--border)',
        borderRadius: 20, padding: 24, width: 400,
      }} onClick={e => e.stopPropagation()}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', marginBottom: 20, letterSpacing: 2 }}>
          {mode === 'create' ? 'NEW VIRTUAL FOLDER' : 'EDIT FOLDER'}
        </div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 9, color: 'var(--text3)', letterSpacing: 2, marginBottom: 6 }}>NAME</div>
          <input
            autoFocus
            className="nh-input"
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && name.trim() && onSave({ name, color, icon, parent_vf_id: parentVfId })}
            placeholder="Folder name..."
          />
        </div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 9, color: 'var(--text3)', letterSpacing: 2, marginBottom: 6 }}>PARENT</div>
          <select
            className="nh-input"
            value={parentVfId ?? ''}
            onChange={e => setParentVfId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">— Root —</option>
            {allFolders
              .filter(f => f.vf_id !== initial?.vf_id)
              .map(f => (
                <option key={f.vf_id} value={f.vf_id}>{f.icon} {f.name}</option>
              ))}
          </select>
        </div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 9, color: 'var(--text3)', letterSpacing: 2, marginBottom: 8 }}>ICON</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {ICONS.map(ic => (
              <button
                key={ic}
                onClick={() => setIcon(ic)}
                style={{
                  background: icon === ic ? 'rgba(103,232,249,0.15)' : 'transparent',
                  border: `1px solid ${icon === ic ? 'var(--cyan)' : 'var(--border)'}`,
                  borderRadius: 8, padding: '4px 8px', fontSize: 18, cursor: 'pointer',
                }}
              >{ic}</button>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 9, color: 'var(--text3)', letterSpacing: 2, marginBottom: 8 }}>COLOR</div>
          <div style={{ display: 'flex', gap: 8 }}>
            {COLORS.map(c => (
              <button
                key={c}
                onClick={() => setColor(c)}
                style={{
                  width: 24, height: 24, borderRadius: '50%', background: c, cursor: 'pointer',
                  border: color === c ? '2px solid white' : '2px solid transparent',
                }}
              />
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button className="nh-btn" onClick={onClose}>CANCEL</button>
          <button
            className="nh-btn primary"
            disabled={!name.trim()}
            onClick={() => onSave({ name, color, icon, parent_vf_id: parentVfId })}
          >
            {mode === 'create' ? 'CREATE' : 'SAVE'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────
export default function VirtualFolders() {
  const { vfolders, setVFolders, vfSelectedId, setVFSelectedId, vfItems, setVFItems } = useStore()

  const [modal, setModal] = useState<{ mode: 'create' | 'edit'; node?: any; parentId?: number | null } | null>(null)
  const [loading, setLoading] = useState(false)

  const loadFolders = useCallback(async () => {
    const data = await listVFolders()
    setVFolders(data.folders || [])
  }, [setVFolders])

  const loadItems = useCallback(async (vfId: number) => {
    setLoading(true)
    try {
      const data = await getVFolderItems(vfId)
      setVFItems(data.items || [])
    } catch { setVFItems([]) }
    setLoading(false)
  }, [setVFItems])

  useEffect(() => { loadFolders() }, [loadFolders])

  useEffect(() => {
    if (vfSelectedId) loadItems(vfSelectedId)
    else setVFItems([])
  }, [vfSelectedId, loadItems, setVFItems])

  const handleSelect = (id: number) => {
    setVFSelectedId(vfSelectedId === id ? null : id)
  }

  const handleSave = async (data: any) => {
    if (modal?.mode === 'create') {
      await createVFolder(data)
    } else if (modal?.node) {
      await updateVFolder(modal.node.vf_id, data)
    }
    setModal(null)
    await loadFolders()
  }

  const handleDelete = async (node: any) => {
    if (!confirm(`Delete "${node.name}" and all its subfolders?`)) return
    await deleteVFolder(node.vf_id)
    if (vfSelectedId === node.vf_id) setVFSelectedId(null)
    await loadFolders()
  }

  const handleRemoveItem = async (itemId: number) => {
    if (!vfSelectedId) return
    await removeItemFromVFolder(vfSelectedId, itemId)
    await loadItems(vfSelectedId)
    await loadFolders()
  }

  const tree = buildTree(vfolders)
  const selectedFolder = vfolders.find(f => f.vf_id === vfSelectedId)

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - var(--topbar-height))', overflow: 'hidden' }}>

      {/* ── Left: tree ── */}
      <aside style={{
        width: 260, flexShrink: 0,
        borderRight: '1px solid var(--border)',
        background: 'var(--bg1)',
        display: 'flex', flexDirection: 'column',
      }}>
        <div style={{ padding: '14px 14px 10px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
          <SectionHeader label="VIRTUAL FOLDERS" accent="var(--purple)" />
          <button
            className="nh-btn primary"
            style={{ width: '100%', fontSize: 10 }}
            onClick={() => setModal({ mode: 'create', parentId: null })}
          >
            + NEW FOLDER
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 8px' }}>
          {tree.length === 0 ? (
            <EmptyState icon="📁" message="No virtual folders yet. Create one to get started." />
          ) : (
            tree.map(node => (
              <FolderNode
                key={node.vf_id}
                node={node}
                depth={0}
                selectedId={vfSelectedId}
                onSelect={handleSelect}
                onCreateChild={(parentId) => setModal({ mode: 'create', parentId })}
                onRename={(n) => setModal({ mode: 'edit', node: n })}
                onDelete={handleDelete}
              />
            ))
          )}
        </div>
      </aside>

      {/* ── Right: items ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {!vfSelectedId ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <EmptyState icon="📂" message="Select a virtual folder to view its files" />
          </div>
        ) : (
          <>
            <div style={{
              padding: '12px 20px', borderBottom: '1px solid var(--border)',
              background: 'var(--bg1)', flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 20 }}>{selectedFolder?.icon}</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: selectedFolder?.color ?? 'var(--cyan)' }}>
                    {selectedFolder?.name}
                  </div>
                  <div style={{ fontSize: 9, color: 'var(--text3)', letterSpacing: 1 }}>
                    {vfItems.length} files
                  </div>
                </div>
              </div>
              <button
                className="nh-btn"
                style={{ fontSize: 9 }}
                onClick={() => setModal({ mode: 'edit', node: selectedFolder })}
              >
                ✎ EDIT FOLDER
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
              {loading ? (
                <div style={{ color: 'var(--text3)', fontSize: 11, padding: 20 }}>Loading...</div>
              ) : vfItems.length === 0 ? (
                <EmptyState icon="📭" message="No files in this folder. Add files from the Search page." />
              ) : (
                vfItems.map((item: any) => (
                  <div
                    key={item.item_id}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 12,
                      padding: '10px 14px', marginBottom: 6,
                      background: 'var(--bg1)', border: '1px solid var(--border)',
                      borderRadius: 14,
                    }}
                  >
                    <div style={{ flex: 1, overflow: 'hidden' }}>
                      <div style={{
                        fontSize: 12, color: 'var(--text)',
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}>
                        {item.file_name}
                      </div>
                      <div style={{
                        fontSize: 9, color: 'var(--text3)', marginTop: 3,
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}>
                        {item.full_path}
                      </div>
                    </div>

                    <div style={{ flexShrink: 0, textAlign: 'right' }}>
                      <Badge group={item.file_type_group || 'other'} />
                      <div style={{ fontSize: 9, color: 'var(--text3)', marginTop: 4 }}>
                        {formatSize(item.size_bytes)}
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                      <button className="nh-btn" style={{ fontSize: 9, padding: '5px 10px' }}
                        onClick={() => openFile(item.item_id)}>OPEN</button>
                      <button className="nh-btn" style={{ fontSize: 9, padding: '5px 10px' }}
                        onClick={() => revealFile(item.item_id)}>REVEAL</button>
                      <button className="nh-btn danger" style={{ fontSize: 9, padding: '5px 10px' }}
                        onClick={() => handleRemoveItem(item.item_id)}>✕</button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </div>

      {modal && (
        <FolderModal
          mode={modal.mode}
          initial={modal.node}
          parentId={modal.parentId}
          allFolders={vfolders}
          onSave={handleSave}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  )
}
