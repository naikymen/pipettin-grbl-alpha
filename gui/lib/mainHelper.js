
function mainHelper () {
  function getItem (name, workspace) {
    if (workspace && workspace.items && workspace.items.length) {
      for (let i = 0; i < workspace.items.length; i++) {
        if (workspace.items[i].name === name) {
          return workspace.items[i];
        }
      }
      return null;
    }
    return null;
  }

  function getContent (name, item) {
    if (item && item.content && item.content.length) {
      for (let i = 0; i < item.content.length; i++) {
        if (item.content[i].name === name) {
          return item.content[i];
        }
      }
      return null;
    }
    return null;
  }

  function getTipVolume (workspace, item) {
    const itemData = getItem(item, workspace);
    if (itemData.platformData.type === 'TIP_RACK' && itemData.platformData.defaultMaxVolume) {
      return itemData.platformData.defaultMaxVolume;
    }
    return 0;
  }

  function getContentsInWorkspace (workspace, itemName, by, contentValue) {
    const contents = [];
    if (workspace && workspace.items && workspace.items.length) {
      for (let i = 0; i < workspace.items.length; i++) {
        if (workspace.items[i].name === itemName || itemName === '') {
          if (workspace.items[i] && workspace.items[i].content && workspace.items[i].content.length) {
            for (let j = 0; j < workspace.items[i].content.length; j++) {
              if (by === 'name') {
                if (workspace.items[i].content[j].name === contentValue) {
                  contents.push({item: workspace.items[i].name, content: workspace.items[i].content[j]});
                }
              } else if (by === 'tag') {
                if ((workspace.items[i].content[j].tags || []).indexOf(contentValue) > -1) {
                  contents.push({item: workspace.items[i].name, content: workspace.items[i].content[j]});
                }
              }
            }
          }
        }// end
      }
    }
    return contents;
  }

  return {
    getItem,
    getContent,
    getContentsInWorkspace,
    getTipVolume
  };
}

module.exports = mainHelper;
