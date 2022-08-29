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
  console.log("Done planning...");

  const tube15Platform = protocol.templateDefinition.tube15Platform;
  const PCRtubePlatform = protocol.templateDefinition.PCRtubePlatform;
  const tube15PlatformIndex = getItemIndexByName(workspace.items, tube15Platform);
  const tubePCRPlatformIndex = getItemIndexByName(workspace.items, PCRtubePlatform);

  // ==== NICO: aca usa protocol.templateDefinition como input para tus algoritmos.
  // TODO magia de nico aca....
  // -------------------------------

  // Puedo acceder al JSON con la syntax de puntitos
  pcrmixplan.master_mix = pcrmixplan.level_mastermix;  // patch name change in R
  let n_reactions = pcrmixplan.master_mix.general_info.n_reactions;
  let components = pcrmixplan.master_mix.total_component_volumes;
  const varcomponents = pcrmixplan.master_mix.variable_component_rxn_volumes;
  const masterCutLevel = pcrmixplan.master_mix.cut_level;

  // Agregar tubos con reactivos y volumenes mínimos-necesarios
  // https://stackoverflow.com/a/34913701/11524079
  l = 0;  // 0.2 tube index counter
  i = 0;  // 1.5 tube index counter
  j = 1;  // step index counter
  // Get amount of columns and rows available in "tube15Platform"
  const ncol = workspace.items[tube15PlatformIndex].platformData.wellsColumns;
  const nrow = workspace.items[tube15PlatformIndex].platformData.wellsRows;
  const ncol2 = workspace.items[tubePCRPlatformIndex].platformData.wellsColumns;
  const nrow2 = workspace.items[tubePCRPlatformIndex].platformData.wellsRows;
  // For each component, add a tube to "tube15Platform"
  // for (const [key, value] of Object.entries(components)) {
  //   // console.log(key, value);
  //   workspace.items[tube15PlatformIndex].content.push(
  //     {
  //       index: i, // increment this. unique by platform
  //       maxVolume: 1500, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
  //       name: key,
  //       // https://stackoverflow.com/a/4228376/11524079
  //       position: {col: i % ncol, row: 1 + Math.floor(i/ncol)},
  //       tags: ['mixcomp', key],
  //       type: 'tube',
  //       volume: value
  //     }
  //   );
  //   i = i + 1
  // }

  // Agregar tubos con reactivos y volumenes mínimos-necesarios
  // DO: Iterate over all mixes.
  for (const [mixname, mix] of Object.entries(pcrmixplan)){
    if(mixname == "component_names"){ continue; }

    // DO: iterate over all components of each mix.
    //console.log("Parsing mix: " + mixname);
    //logObject(mix);
    for (const [compname, compvol] of Object.entries(mix.mix_component_volumes)){
      // DO: add component tube to rack.

      // If the component is a mix, skip it, it will be added in a different loop below).
      if( pcrmixplan.hasOwnProperty(compname) ){
        console.log("pcrmixplan.hasOwnProperty(compname) SKIPPING: " + compname);
        continue;
      } else {
        console.log("pcrmixplan.hasOwnProperty(compname) ADDING: " + compname);
      }

      // If the component of this mix is not variable, (syntax from: https://stackoverflow.com/a/455366/11524079)
      if( !(varcomponents.hasOwnProperty(compname)) ){
        // There is no need to check if it already exists in the rack,
        // simply add a tube.
        workspace.items[tube15PlatformIndex].content.push(
          {
            index: i+1, // increment this. unique by platform
            maxVolume: 1500, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
            name: compname,
            // https://stackoverflow.com/a/4228376/11524079
            position: {col: 1 + (i % ncol), row: 1 + Math.floor(i/ncol)},
            tags: ['mixcomp', compname],
            type: 'tube',
            volume: compvol
          }
        );
        i = i + 1;
      } else {
        // If the component _is_ variable, then do something else.
        // Get the varcomp name,
        let varcompname = mix.mix_component_names[compname];
        // check if the variable component already exists,
        if( workspace.items[tube15PlatformIndex].content.hasOwnProperty(varcompname) ){
          // and simply add volume to it.
          workspace.items[tube15PlatformIndex].content[varcompname].volume += compvol;
          // Or if the variable component is not in the tube rack yet,
        } else {
          // then add it now, using the variable name of the component "type".
          // (i.e. "template1" variant of component type "template").
          workspace.items[tube15PlatformIndex].content.push(
            {
              index: i+1, // increment this. unique by platform
              maxVolume: 1500, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
              name: varcompname,
              // https://stackoverflow.com/a/4228376/11524079
              position: {col: 1 + (i % ncol), row: 1 + Math.floor(i/ncol)},
              tags: ['mixcomp', compname],
              type: 'tube',
              volume: compvol
            }
          );
          i = i + 1;
        }
      }  // DONE: adding a component tube.
    }  // DONE: adding all component tubes for this mix.
  }  // DONE: adding all component tubes to rack.

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
  // insert MASTER MIX TUBE in the 1.5ml platform
  // workspace.items[tube15PlatformIndex].content.push(
  //   {
  //     index: i, // increment this. unique by platform
  //     maxVolume: 1500, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
  //     name: 'master_mix',
  //     position: {col: i % ncol, row: 1 + Math.floor(i/ncol)},
  //     tags: ['master_mix'],
  //     type: 'tube',
  //     volume: 0
  //   }
  // );
  // i = i + 1;

  // Funcion generadora de steps a partir de un template
  function stepTemplateN2T(order, sourcePlatformName, sourceItemName, targetPlatformName, targetItemTag, volume){
    let template = {
      'order': order, // increment this for each step
      'name': 'step' + order, // step name
      'type': 'SIMPLE_PIPETTIN', // enum
      'definition': {
        'source': {
          'item': sourcePlatformName, // bucar en esta plataforma (debes usar protocol.templateDefinition.tube15Platform o protocol.templateDefinition.PCRtubePlatform)
          'by': 'name', // select by name
          'value': sourceItemName, // select with this name
          'treatAs': 'same' // cuando el by es por name, solo tiene sentido poner "same" aca
        },
        'target': {
          'item': targetPlatformName, // busca en esta plataforma destino (debes usar protocol.templateDefinition.tube15Platform o protocol.templateDefinition.PCRtubePlatform)
          'by': 'tag', // busca por tag
          'value': targetItemTag // con este tag
        },
        'volume': {
          'type': 'fixed_each', // si pones fixed_each es 5ul fijo para cada target encontrado
                                // si pones fixed_total serian 5ul en total sumando todos los targets encontrados
                                // si pones type for_each_target_tag y agregas "tag" : "otrotag" serian 5*(cosas_con_tag_otrotag)ul en cada target. Es una forma de calcular un total pero basado en otro tag que no es el source
          'value': volume
        },
        'tip': {
          'mode': 'isolated_source_only', // solo cambia el tip antes de agarrar del source. despues dropea en los targets sin cambiar de tip.
          'item': protocol.templateDefinition.tipsPlatform,
          'discardItem': protocol.templateDefinition.trashPlatform
        }
      }
    }
    return template;
  }
  // Lo mismo pero nombre a nombre
  function stepTemplateN2N(order, sourcePlatformName, sourceItemName, targetPlatformName, targetItemTag, volume){
    let template = stepTemplateN2T(order, sourcePlatformName, sourceItemName, targetPlatformName, targetItemTag, volume);
    template.definition.target.by = "name";
    return template;
  }

  // Agregar tubos de cada mix y pasos para pipetearlas
  k = masterCutLevel;
  // Iterar por "k" asegura que las mixes más generales se preparen primero.
  i=i+1; // Offset para que quede lindo
  while(k > 0){
    for (const [mixname, mix] of Object.entries(pcrmixplan)){
      // console.log("Parsing mix: " + mixname);
      // Si es un derivado del nivel anterior, agregar un tubo y los steps
      if(mix.cut_level == k){
          workspace.items[tube15PlatformIndex].content.push(
           {
             index: i+1-1, // resto el offset para que quede lindo
             maxVolume: 1500, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
             name: mixname,
             position: {col: 1 + (i % ncol), row: 1 + Math.floor(i/ncol)},
             tags: ['mix', 'mixlevel' + k],
             type: 'tube',
             volume: 0
           }
         );
         i = i + 1;
         // Get component volumes for this mixx tube, and add steps accordingly:
         let mixComponents = mix.mix_component_volumes
         for (const [compname, compvol] of Object.entries(mixComponents)){

           if( !(mix.hasOwnProperty("mix_component_names")) ){
             // This handles the mastermix
             console.log("Parsing compname from master: " + compname);
             var newstep = stepTemplateN2N(j, tube15Platform, compname, tube15Platform, mixname, compvol);

           } else if( mix.mix_component_names.hasOwnProperty(compname) ){
             // This handles variable components
             console.log("Parsing variable compname: " + compname);
             var newstep = stepTemplateN2N(j, tube15Platform, mix.mix_component_names[compname], tube15Platform, mixname, compvol);

           } else {
             // This is the default
             console.log("Parsing compname default: " + mixname);
             var newstep = stepTemplateN2N(j, tube15Platform, compname, tube15Platform, mixname, compvol);
           }

           protocol.steps.push(newstep);
           j = j + 1;
         }
      }

      // ACA HAY QUE CHEQUEAR SI AGREGAR TUBOS DE PCR??
      // LEVEL=1 puede no servir si hay un grupo más "simple" que otros.

    };
    k = k - 1;
  };

  // Ahora busco los "terminal" tubes con cut=0, y los pongo en la gradilla de PCR
  for (const [mixname, mix] of Object.entries(pcrmixplan)){
    // Si es un derivado del nivel anterior, agregar un tubo y los steps
    if(mix.cut_level == 0){
        workspace.items[tubePCRPlatformIndex].content.push(
         {
           index: l+1, // increment this. unique by platform
           maxVolume: 200, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
           name: mix.labels,
           position: {col: 1 + (l % ncol2), row: 1 + Math.floor(l/ncol2)},
           tags: ['reaction', 'mixlevel' + k],
           type: 'tube',
           volume: 0
         }
       );
       l = l + 1;
       // Get component volumes for this mixx tube, and add steps accordingly:
       let mixComponents = mix.mix_component_volumes
       for (const [compname, compvol] of Object.entries(mixComponents)){
         if( !(mix.hasOwnProperty("mix_component_names")) ){
           // This handles the mastermix
           console.log("Parsing compname from master: " + compname);
           var newstep = stepTemplateN2N(j, tube15Platform, compname, PCRtubePlatform, mix.labels, compvol);

         } else if( mix.mix_component_names.hasOwnProperty(compname) ){
           // This handles variable components
           console.log("Parsing variable compname: " + compname);
           var newstep = stepTemplateN2N(j, tube15Platform, mix.mix_component_names[compname], PCRtubePlatform, mix.labels, compvol);

         } else {
           // This is the default
           console.log("Parsing compname default: " + mix.labels);
           var newstep = stepTemplateN2N(j, tube15Platform, compname, PCRtubePlatform, mix.labels, compvol);
         }
         protocol.steps.push(newstep);
         j = j + 1;
       }
    }

    // ACA HAY QUE CHEQUEAR SI AGREGAR TUBOS DE PCR??
    // LEVEL=1 puede no servir si hay un grupo más "simple" que otros.

  };
  // insert TUBE in the PCR platform
  // workspace.items[tubePCRPlatformIndex].content.push(
  //   {
  //     index: 1, // increment this
  //     maxVolume: 200, // in workspace.items[tube15PlatformIndex].platformData tenes la info de la paltaforma. ej .defaultMaxVolume
  //     name: 'nameUniqueHere',
  //     position: {col: 1, row: 1},
  //     tags: ['pcrtube'],
  //     type: 'tube',
  //     volume: 20
  //   }
  // );

  // ---------------------------------------------
  // ejemplos de como agregar step al protocolo:

  // agarrar de un source con name "nameMustBeUnique" lo necesario para poner 5ul en cada target con tag "pcrtube"
  // let newstep = stepTemplateN2T(j, tube15Platform, "water", tube15Platform, "master_mix", 10);
  // protocol.steps.push(newstep);
  // j = j + 1;

  // agarrar de varios sources con el mismo tag y tratarlos como una unidad. Dropear en tubos con X tag
  // protocol.steps.push(
  //   {
  //     'order': 2, // increment this for each step
  //     'name': 'step2', // step name
  //     'type': 'SIMPLE_PIPETTIN', // enum
  //     'definition': {
  //       'source': {
  //         'item': '3x3_1.5_rack 1', // bucar en esta plataforma (debes usar protocol.templateDefinition.tube15Platform o protocol.templateDefinition.PCRtubePlatform)
  //         'by': 'tag', // select by tag
  //         'value': 'medium', // select with this tag
  //         'treatAs': 'same' // cuando el by es por tag, si detectamos mas de 1 tubo, podemos tratarlos como una unica cosa o cosas distintas. "same" los va a tratar como una unica unidad
  //                           // si usamos "for_each" va a iterar este step por cada source seleccionado
  //       },
  //       'target': {
  //         'item': '12x8_0.2_rack 1', // busca en esta plataforma destino (debes usar protocol.templateDefinition.tube15Platform o protocol.templateDefinition.PCRtubePlatform)
  //         'by': 'tag', // busca por tag
  //         'value': 'pcrtube' // con este tag
  //       },
  //       'volume': {
  //         'type': 'fixed_each', // si pones fixed_each es 5ul fijo para cada target encontrado
  //                               // si pones fixed_total serian 5ul en total sumando todos los targets encontrados
  //                               // si pones type for_each_target_tag y agregas "tag" : "otrotag" serian 5*(cosas_con_tag_otrotag)ul en cada target. Es una forma de calcular un total pero basado en otro tag que no es el source
  //         'value': '10'
  //       },
  //       'tip': {
  //         'mode': 'isolated_targets', // "isolated_targets" Will change the tip after touch a target
  //                                     // "reuse" Will always re-use the tip in this step
  //                                     // "reuse_same_source" Will re-use the tip to load multiple times from the same source if target will be the same. Will change the tip for different targets
  //                                     // "isolated_source_only" Will change the tip before touch a source. May touch several targets with the same tip
  //         'item': protocol.templateDefinition.tipsPlatform, // nombre de la plataforma que tiene los tips
  //         'discardItem': protocol.templateDefinition.trashPlatform // nombre de la plataforma para descartar tips
  //       }
  //     }
  //   }
  // );

  // no importa que retorna esta funcion. Las modificaciones que hagas a los objetos protocol y worksspace van a ser guardadas.

  //console.log('Final Workspace:');
  //logObject(workspace);

  console.log('Final Protocol:');
  logObject(protocol);

  return {protocol, workspace};
}

const pcrMixLib = {
  process
};

module.exports = pcrMixLib;
