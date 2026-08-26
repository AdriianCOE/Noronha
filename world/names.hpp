// Noronha player-facing map labels.
// Internal class identifiers, coordinates, types and radii are intentionally
// preserved from the current world config. Only display names are simplified.
// This file is staged for a later #include after the validated local world
// config is synchronized with Git.
class Names
{
    // Vilas
    class Vila_Remedios       { name="Remedios";        position[]={7777.94,7489.46}; type="Capital"; radiusA=400.00; radiusB=400.00; angle=0; };
    class Vila_Trinta         { name="Trinta";          position[]={8187.84,6967.93}; type="City";    radiusA=239.04; radiusB=183.94; angle=0; };
    class Vila_Floresta_Velha { name="Floresta Velha"; position[]={7513.63,7091.27}; type="Village"; radiusA=298.79; radiusB=229.92; angle=0; };
    class Vila_Floresta_Nova  { name="Floresta Nova";  position[]={7669.26,6824.57}; type="Village"; radiusA=298.79; radiusB=229.92; angle=0; };
    class Vila_Mulungu        { name="Mulungu";         position[]={5302.92,6437.34}; type="Village"; radiusA=239.04; radiusB=180.00; angle=0; };
    class Vila_Coria          { name="Coria";           position[]={5317.95,5830.23}; type="Village"; radiusA=239.04; radiusB=183.94; angle=0; };
    class Vila_Conceicao      { name="Conceicao";       position[]={7149.84,7420.70}; type="Village"; radiusA=152.98; radiusB=117.72; angle=0; };
    class Vila_Tres_Paus      { name="Tres Paus";       position[]={6386.13,6254.65}; type="Village"; radiusA=191.23; radiusB=147.15; angle=0; };
    class Vila_Quixaba        { name="Quixaba";         position[]={4615.87,5886.62}; type="Village"; radiusA=191.23; radiusB=147.15; angle=0; };
    class Vila_Boldro         { name="Boldro";          position[]={6107.69,6661.86}; type="Village"; radiusA=280.00; radiusB=220.00; angle=0; };

    // Infraestrutura
    class Aeroporto         { name="Aeroporto";  position[]={5845.81,5907.83}; type="IndustrialSite"; radiusA=239.04; radiusB=183.94; angle=0; };
    class Vila_Militar_FAB  { name="Base Aerea"; position[]={5934.72,5496.17}; type="LocalOffice";    radiusA=298.79; radiusB=229.92; angle=0; };
    class Radar_Aeronautica { name="Radar";      position[]={8867.31,6830.66}; type="Local";          radiusA=122.39; radiusB=94.18;  angle=0; };
    class Forte_Noronha     { name="Forte";      position[]={7883.44,7882.86}; type="Ruin";           radiusA=78.33;  radiusB=60.27;  angle=0; };
    class Porto             { name="Porto";      position[]={9021.95,8296.21}; type="Marine";         radiusA=152.98; radiusB=117.72; angle=0; };
    class Hospital_Noronha  { name="Hospital";   position[]={7600.00,7300.00}; type="LocalOffice";    radiusA=60.00;  radiusB=60.00;  angle=0; };
    class Centro_Visitantes { name="Visitantes"; position[]={7200.00,7100.00}; type="LocalOffice";    radiusA=50.00;  radiusB=50.00;  angle=0; };

    // Praias
    class Praia_Cacimba   { name="Cacimba";          position[]={4662.59,6550.35}; type="Local"; radiusA=122.39; radiusB=94.18;  angle=0; };
    class Praia_Boldro    { name="Praia Boldro";     position[]={6016.48,7142.68}; type="Local"; radiusA=97.91;  radiusB=75.34;  angle=0; };
    class Praia_Atalaia   { name="Atalaia";          position[]={8016.25,5854.31}; type="Local"; radiusA=152.98; radiusB=117.72; angle=0; };
    class Praia_Sueste    { name="Sueste";           position[]={6289.14,4827.86}; type="Local"; radiusA=122.39; radiusB=94.18;  angle=0; };
    class Praia_Leao      { name="Leao";             position[]={4818.69,4339.22}; type="Local"; radiusA=191.23; radiusB=147.15; angle=0; };
    class Praia_Sancho    { name="Sancho";           position[]={4159.94,6053.32}; type="Local"; radiusA=122.39; radiusB=94.18;  angle=0; };
    class Praia_Americano { name="Americano";        position[]={5380.93,6899.57}; type="Local"; radiusA=62.66;  radiusB=48.22;  angle=0; };
    class Praia_Bode      { name="Bode";             position[]={5164.33,6769.49}; type="Local"; radiusA=78.33;  radiusB=60.27;  angle=0; };
    class Praia_Conceicao { name="Praia Conceicao";  position[]={7400.00,7650.00}; type="Local"; radiusA=150.00; radiusB=120.00; angle=0; };
    class Praia_Cachorro  { name="Cachorro";         position[]={7777.17,7762.52}; type="Local"; radiusA=100.00; radiusB=100.00; angle=0; };

    // Natureza
    class Acude_Xareu      { name="Xareu";           position[]={5701.93,4869.10}; type="Local";  radiusA=132.69; radiusB=102.11; angle=0; };
    class Piscina_Natural  { name="Piscina Natural"; position[]={8150.00,5720.00}; type="Local";  radiusA=60.00;  radiusB=60.00;  angle=0; };
    class Enseada_Boto     { name="Golfinhos";       position[]={6720.00,7450.00}; type="Marine"; radiusA=180.00; radiusB=150.00; angle=0; };
    class Baia_Porcos      { name="Porcos";          position[]={4405.46,6405.85}; type="Marine"; radiusA=100.00; radiusB=100.00; angle=0; };
    class Cemiterio_Quixaba{ name="Cemiterio";       position[]={4700.00,5800.00}; type="Ruin";   radiusA=40.00;  radiusB=40.00;  angle=0; };

    // Morros
    class Rocha_Nega        { name="Pico";        position[]={6594.60,7163.40}; type="RockArea"; radiusA=160.00; radiusB=130.00; angle=360; };
    class Morro_Dois_Irmaos { name="Dois Irmaos"; position[]={4416.23,6661.29}; type="RockArea"; radiusA=100.00; radiusB=100.00; angle=0; };

    // Mirantes
    class Mirante_Forte_Boldro { name="Forte Boldro"; position[]={5535.67,6924.67}; type="ViewPoint"; radiusA=62.66;  radiusB=48.22;  angle=0; };
    class Ponta_Air_France     { name="Air France";    position[]={9157.75,8674.32}; type="ViewPoint"; radiusA=152.98; radiusB=117.72; angle=0; };
    class Pontinha             { name="Pontinha";      position[]={9684.66,6438.10}; type="ViewPoint"; radiusA=239.04; radiusB=183.94; angle=0; };
    class Ponta_Sapata         { name="Sapata";        position[]={983.61,3734.55};  type="ViewPoint"; radiusA=239.04; radiusB=183.94; angle=0; };
    class Buraco_Raquel        { name="Raquel";        position[]={9229.12,8436.44}; type="ViewPoint"; radiusA=80.00;  radiusB=80.00;  angle=0; };

    // Cultura
    class Capela_Sao_Pedro { name="Sao Pedro"; position[]={9132.22,8389.56}; type="Local"; radiusA=50.00; radiusB=50.00; angle=0; };
    class Museu_Tubarao    { name="Tubarao";   position[]={9114.88,8247.74}; type="Local"; radiusA=50.00; radiusB=50.00; angle=0; };

    // Ilhas secundarias
    class Ilha_Meio        { name="Meio";        position[]={9771.58,9924.72}; type="Local"; radiusA=239.04; radiusB=183.94; angle=0; };
    class Ilha_Sela_Gineta { name="Sela Gineta"; position[]={9702.95,9394.66}; type="Local"; radiusA=122.39; radiusB=94.18;  angle=0; };
    class Ilha_Rasa        { name="Rasa";        position[]={9368.55,9039.43}; type="Local"; radiusA=97.91;  radiusB=75.34;  angle=0; };
    class Ilha_Sao_Jose    { name="Sao Jose";    position[]={8844.17,9119.80}; type="Local"; radiusA=78.33;  radiusB=60.27;  angle=0; };
};
