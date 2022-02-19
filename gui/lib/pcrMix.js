const util = require('util');
// Import function to execute a system call synchronously
const execSync = require('child_process').execSync;
// Import function to write a file
const fs = require('fs');

function logObject (obj) {
  console.log(util.inspect(obj, false, null, true));
}

function getItemIndexByName (items, name) {
  for (let i = 0; i < items.length; i++) {
    if (items[i].name === name) {
      return i;
    }
  }
}

// Define function to interact with the Rscript PCRmix planner
// This should be ported to JS in the future.
async function pcrMixPlannerr(protocol) {
    // Convert dictionary to a JSON string
    let protocolJSON = JSON.stringify(protocol);  // https://stackabuse.com/reading-and-writing-json-files-with-node-js/
    fs.writeFileSync('/tmp/planerr_input.json', protocolJSON);
    // Run the R code
    console.log('Planning PCR mix protocol using R');
    code = execSync('Rscript --vanilla /home/pi/pipettin-grbl/Rscripts/pcr_planner.R /tmp/planerr_input.json /tmp/planerr_output.json');
    // Read the output
    let outputJSON = fs.readFileSync('/tmp/planerr_output.json');
    let plan = JSON.parse(outputJSON);
    // Return the pipetting planner output
    return plan
}

async function process (protocol, workspace) {
  console.log('==init====process PCR Mix template data=======');
  console.log('Received Protocol:');
  logObject(protocol);
  console.log('Received Workspace:');
  logObject(workspace);

  let pcrmixplan = await pcrMixPlannerr(protocol);
  console.log(pcrmixplan);

  const tube15PlatformIndex = getItemIndexByName(workspace.items, protocol.templateDefinition.tube15Platform);
  const tubePCRPlatformIndex = getItemIndexByName(workspace.items, protocol.templateDefinition.PCRtubePlatform);

  // ==== NICO: aca usa protocol.templateDefinition como input para tus algoritmos.
  // TODO magia de nico aca....
  // -------------------------------

  // Puedo acceder al JSON con la syntax de puntitos
  let n_reactions = pcrmixplan.master_mix.general_info.n_reactions
  let components = pcrmixplan.master_mix.total_component_volumes

  // https://stackoverflow.com/a/34913701/11524079
  i = 1
  let ncol = workspace.items[tube15PlatformIndex].platformData.wellsColumns
  let nrow = workspace.items[tube15PlatformIndex].platformData.wellsRows
  for (const [key, value] of Object.entries(components)) {
    console.log(key, value);
    workspace.items[tube15PlatformIndex].content.push(
      {
        index: i, // increment this. unique by platform
        maxVolume: 1500, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
        name: key,
        // https://stackoverflow.com/a/4228376/11524079
        position: {col: i % ncol, row: 1 + Math.floor(i/ncol)},
        tags: ['mixcomp', key],
        type: 'tube',
        volume: value
      }
    );
    i = i + 1
  }

  // Aca te pongo ejemplos de como agregar tubos a las plataformas:

  //// insert TUBE in the 1.5ml platform
  //workspace.items[tube15PlatformIndex].content.push(
  //  {
  //    index: 1, // increment this. unique by platform
  //    maxVolume: 1500, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
  //    name: 'nameMustBeUnique',
  //    position: {col: 1, row: 1},
  //    tags: ['untag'],
  //    type: 'tube',
  //    volume: 40
  //  }
  //);
  //
  //// insert TUBE in the 1.5ml platform
  //workspace.items[tube15PlatformIndex].content.push(
  //  {
  //    index: 2, // increment this. unique by platform
  //    maxVolume: 1500, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
  //    name: 'medium1',
  //    position: {col: 2, row: 1},
  //    tags: ['medium'],
  //    type: 'tube',
  //    volume: 1500
  //  }
  //);
  //
  //// insert TUBE in the 1.5ml platform
  //workspace.items[tube15PlatformIndex].content.push(
  //  {
  //    index: 3, // increment this. unique by platform
  //    maxVolume: 1500, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
  //    name: 'medium2',
  //    position: {col: 3, row: 1},
  //    tags: ['medium'],
  //    type: 'tube',
  //    volume: 1500
  //  }
  //);

  // insert TUBE in the PCR platform
  workspace.items[tubePCRPlatformIndex].content.push(
    {
      index: 1, // increment this
      maxVolume: 200, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
      name: 'nameUniqueHere',
      position: {col: 1, row: 1},
      tags: ['pcrtube'],
      type: 'tube',
      volume: 20
    }
  );

  // ---------------------------------------------
  // ejemplos de como agregar step al protocolo:

  // agarrar de un source con name "nameMustBeUnique" lo necesario para poner 5ul en cada target con tag "pcrtube"
  protocol.steps.push(
    {
      'order': 1, // increment this for each step
      'name': 'step1', // step name
      'type': 'SIMPLE_PIPETTIN', // enum
      'definition': {
        'source': {
          'item': '3x3_1.5_rack 1', // bucar en esta plataforma (debes usar protocol.templateDefinition.tube15Platform o protocol.templateDefinition.PCRtubePlatform)
          'by': 'name', // select by name
          'value': 'nameMustBeUnique', // select with this name
          'treatAs': 'same' // cuando el by es por name, solo tiene sentido poner "same" aca
        },
        'target': {
          'item': '12x8_0.2_rack 1', // busca en esta plataforma destino (debes usar protocol.templateDefinition.tube15Platform o protocol.templateDefinition.PCRtubePlatform)
          'by': 'tag', // busca por tag
          'value': 'pcrtube' // con este tag
        },
        'volume': {
          'type': 'fixed_each', // si pones fixed_each es 5ul fijo para cada target encontrado
                                // si pones fixed_total serian 5ul en total sumando todos los targets encontrados
                                // si pones type for_each_target_tag y agregas "tag" : "otrotag" serian 5*(cosas_con_tag_otrotag)ul en cada target. Es una forma de calcular un total pero basado en otro tag que no es el source
          'value': '5'
        },
        'tip': {
          'mode': 'isolated_source_only', // solo cambia el tip antes de agarrar del source. despues dropea en los targets sin cambiar de tip.
          'item': protocol.templateDefinition.tipsPlatform,
          'discardItem': protocol.templateDefinition.trashPlatform
        }
      }
    }
  );

  // agarrar de varios sources con el mismo tag y tratarlos como una unidad. Dropear en tubos con X tag
  protocol.steps.push(
    {
      'order': 2, // increment this for each step
      'name': 'step2', // step name
      'type': 'SIMPLE_PIPETTIN', // enum
      'definition': {
        'source': {
          'item': '3x3_1.5_rack 1', // bucar en esta plataforma (debes usar protocol.templateDefinition.tube15Platform o protocol.templateDefinition.PCRtubePlatform)
          'by': 'tag', // select by tag
          'value': 'medium', // select with this tag
          'treatAs': 'same' // cuando el by es por tag, si detectamos mas de 1 tubo, podemos tratarlos como una unica cosa o cosas distintas. "same" los va a tratar como una unica unidad
                            // si usamos "for_each" va a iterar este step por cada source seleccionado
        },
        'target': {
          'item': '12x8_0.2_rack 1', // busca en esta plataforma destino (debes usar protocol.templateDefinition.tube15Platform o protocol.templateDefinition.PCRtubePlatform)
          'by': 'tag', // busca por tag
          'value': 'pcrtube' // con este tag
        },
        'volume': {
          'type': 'fixed_each', // si pones fixed_each es 5ul fijo para cada target encontrado
                                // si pones fixed_total serian 5ul en total sumando todos los targets encontrados
                                // si pones type for_each_target_tag y agregas "tag" : "otrotag" serian 5*(cosas_con_tag_otrotag)ul en cada target. Es una forma de calcular un total pero basado en otro tag que no es el source
          'value': '10'
        },
        'tip': {
          'mode': 'isolated_targets', // "isolated_targets" Will change the tip after touch a target
                                      // "reuse" Will always re-use the tip in this step
                                      // "reuse_same_source" Will re-use the tip to load multiple times from the same source if target will be the same. Will change the tip for different targets
                                      // "isolated_source_only" Will change the tip before touch a source. May touch several targets with the same tip
          'item': protocol.templateDefinition.tipsPlatform, // nombre de la plataforma que tiene los tips
          'discardItem': protocol.templateDefinition.trashPlatform // nombre de la plataforma para descartar tips
        }
      }
    }
  );

  // no importa que retorna esta funcion. Las modificaciones que hagas a los objetos protocol y worksspace van a ser guardadas.
  return {protocol, workspace};
}

const pcrMixLib = {
  process
};

module.exports = pcrMixLib;
