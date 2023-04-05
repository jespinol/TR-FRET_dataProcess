import localsolver.LocalSolver;

import java.io.*;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        System.out.println("Program assumes ONE set of donor+ and donor- per file and ONE well without acceptor (which is at the last position)");
        HashMap<String, String> dataset = getDatasetInfo();
        HashMap<String, HashMap<Integer, ArrayList<Integer>>> rawSignal = openFileAndParseSignal(dataset.get("path"));
        HashMap<Integer, ArrayList<Float>> correctedSignal = processSignal(rawSignal);
        HashMap<Integer, ArrayList<Float>> normalizedSignal = normalizeSignal(correctedSignal);
        ArrayList<Float> concentrations = processConcentrations(normalizedSignal.get(1).size(), dataset.get("concentration"));
        correctedSignal.put(0, concentrations);
        normalizedSignal.put(0, concentrations);
        boolean areThereStats = false;
        if (normalizedSignal.size() > 2) {
            addStatistics(correctedSignal);
            addStatistics(normalizedSignal);
            areThereStats = true;
        }
//        LocalSolver localSolver =  new LocalSolver();
//        CurveFitting fitting = new CurveFitting(localSolver, normalizedSignal, areThereStats);
//        fitting.runSolver();
        System.out.println("\n------------------------- Corrected data -------------------------");
        printProcessedData(correctedSignal, areThereStats);
        System.out.println("\n------------------------- Corrected and normalized data -------------------------");
        printProcessedData(normalizedSignal, areThereStats);
    }

    private static HashMap<String, String> getDatasetInfo() {
        HashMap<String, String> output = new HashMap<>();
        Scanner scanner = new Scanner(System.in);
        System.out.println("File example /Users/jespinol/Downloads/trfret_eml");
        System.out.print("Enter the path of the directory/file to process: ");
        output.put("path", scanner.nextLine());
        System.out.print("Enter highest concentration in mM: ");
        output.put("concentration", scanner.nextLine());
        return output;
    }

    public static HashMap<String, HashMap<Integer, ArrayList<Integer>>> openFileAndParseSignal(String inputFileOrDirectory) {
        BufferedReader reader;
        FileWriter writer = null;
        HashMap<Integer, ArrayList<Integer>> rawData615 = new HashMap<>();
        HashMap<Integer, ArrayList<Integer>> rawData665 = new HashMap<>();
        try {
            boolean directoryProvided = !inputFileOrDirectory.endsWith(".csv");
            File directory = new File(directoryProvided ? inputFileOrDirectory : inputFileOrDirectory.substring(0, inputFileOrDirectory.lastIndexOf("/")));
            File[] directoryFiles = directory.listFiles();
            String path = directory.getAbsolutePath();
//            String outputFileName = directoryProvided ? path.substring(path.lastIndexOf("/") + 1) : inputFileOrDirectory.substring(inputFileOrDirectory.lastIndexOf("/") + 1, inputFileOrDirectory.lastIndexOf("."));
//            writer = new FileWriter(path + "/" + outputFileName + ".txt");
            int repeat = 1;
            if (directoryProvided && directoryFiles != null) {
                for (File file : directoryFiles) {
                    if (file.isFile() && file.getName().endsWith(".csv")) {
                        reader = new BufferedReader(new FileReader(file));
                        String line = reader.readLine();
                        rawData615.put(repeat, parseData(reader, line, true));
                        line = reader.readLine();
                        rawData665.put(repeat, parseData(reader, line, false));
                        repeat++;
                    }
                }
            } else {
                reader = new BufferedReader(new FileReader(inputFileOrDirectory));
                String line = reader.readLine();
                rawData615.put(repeat, parseData(reader, line, true));
                line = reader.readLine();
                rawData665.put(repeat, parseData(reader, line, false));
            }
        } catch (IOException e) {
            System.out.println("Input directory/file does not exist or does not contain a valid csv file.");
        }
        HashMap<String, HashMap<Integer, ArrayList<Integer>>> rawData = new HashMap<>();
        rawData.put("615", rawData615);
        rawData.put("665", rawData665);
        return rawData;
    }

    public static ArrayList<Integer> parseData(BufferedReader reader, String line, boolean firstRound) throws IOException {
        ArrayList<Integer> dataArr = new ArrayList<>();
        while (firstRound ? !line.equals("") : line != null) {
            dataArr.add(Integer.valueOf(line));
            line = reader.readLine();
        }
        return dataArr;
    }

    private static HashMap<Integer, ArrayList<Float>> processSignal(HashMap<String, HashMap<Integer, ArrayList<Integer>>> data) {
        HashMap<Integer, ArrayList<Float>> output = new HashMap<>();
        for (int i = 1; i <= data.get("665").size(); i++) {
            output.put(i, correctSignal(data.get("615").get(i), data.get("665").get(i)));
        }
        return output;
    }

    private static ArrayList<Float> correctSignal(ArrayList<Integer> data615, ArrayList<Integer>data665) {
        ArrayList<Float> output = new ArrayList<>();
        int lastIndex = data615.size() - 1;
        float alpha = (float) data665.get(lastIndex) / data615.get(lastIndex);
        int firstIndexOfDonorPlus = (data615.size() / 2);
        for (int p = firstIndexOfDonorPlus, m = 0; p < lastIndex; p++, m++) {
            float corrected = ((data665.get(p) - (alpha * data615.get(p))) - (data665.get(m) - (alpha * data615.get(m))));
            output.add(corrected);
        }
        return output;
    }

    private static HashMap<Integer, ArrayList<Float>> normalizeSignal(HashMap<Integer, ArrayList<Float>> data) {
        HashMap<Integer, ArrayList<Float>> output = new HashMap<>();
        for (Integer key : data.keySet()) {
            ArrayList<Float> currentRepeat = (ArrayList<Float>) data.get(key).clone();
            float[] fMaxMin = findSignalMaxMin(currentRepeat);
            currentRepeat.replaceAll(signal -> (signal - fMaxMin[1]) / (fMaxMin[0] - fMaxMin[1]));
            output.put(key, currentRepeat);
        }
        return output;
    }

    private static float[] findSignalMaxMin(ArrayList<Float> data) {
        float[] output = new float[2];
        float fMax = data.get(0);
        float fMin = data.get(0);
        for (int i = 1; i < data.size(); i++) {
            float currentValue = data.get(i);
            if (data.get(i) > fMax) {
                fMax = currentValue;
            }
            if (data.get(i) < fMin) {
                fMin = currentValue;
            }
        }
        output[0] = fMax;
        output[1] = fMin;
        return output;
    }

    private static ArrayList<Float> processConcentrations(int num, String concentration) {
        ArrayList<Float> output = new ArrayList<>();
        float currentConcentration = Float.parseFloat(concentration) * 1000;
        for (int i = 1; i <= num; i++) {
            output.add(currentConcentration);
            currentConcentration = currentConcentration / 2;
        }
        return output;
    }

    private static void addStatistics(HashMap<Integer, ArrayList<Float>> data) {
        int repeatNum = data.size() - 1;
        ArrayList<Float> average = new ArrayList<>();
        ArrayList<Float> stDev = new ArrayList<>();
        float sum = 0;
        float sd = 0;
        for (int i = 0; i < data.get(0).size(); i++) {
            for (int j = 1; j <= repeatNum; j++) {
                sum += data.get(j).get(i);
            }
            float mean = sum / repeatNum;
            average.add(mean);
            for (int j = 1; j <= repeatNum; j++) {
                sd += Math.pow(data.get(j).get(i) - mean, 2);
            }
            sd = (float) Math.sqrt(sd / repeatNum);
            stDev.add(sd);
            sum = 0;
            sd = 0;
        }
        int nextIndex = data.size();
        data.put(nextIndex, average);
        data.put(nextIndex + 1, stDev);
    }

    private static void printProcessedData(HashMap<Integer, ArrayList<Float>> data, boolean areThereStats) {
        int columns = data.size();
        int rows = data.get(0).size();
        int repeats = areThereStats ? (data.size() - 3) : 1;
        System.out.print("L (nM)\t");
        System.out.print("log(L)\t");
        for (int repeat = 1; repeat <= repeats; repeat++) {
            System.out.print("Rep " + repeat + "\t");
        }
        if (areThereStats) {
            System.out.print("Ave\t");
            System.out.print("StDev.P\t");
        }
        System.out.print("\n");
        DecimalFormat oneDec = new DecimalFormat("0.0");
        DecimalFormat twoDec = new DecimalFormat("0.00");
        DecimalFormat threeDec = new DecimalFormat("0.0000");
        for (int row = 0; row < rows; row++) {
            float concentration = data.get(0).get(row);
            double logConcentration = Math.log10(data.get(0).get(row));
            if (concentration >= 1000) {
                System.out.printf("%.0f\t", concentration);
            } else if (concentration >= 100) {
                System.out.printf("%.1f\t", concentration);
            } else if (concentration >= 10) {
                System.out.printf("%.2f\t", concentration);
            } else {
                System.out.printf("%.3f\t", concentration);
            }
            System.out.printf("%.3f\t", logConcentration);
            for (int col = 1; col < columns; col++) {
                float value = data.get(col).get(row);
                if (value <= 100) {
                    System.out.printf("%.3f\t", value);
                } else {
                    System.out.printf("%.1f\t", value);
                }
            }
            System.out.print("\n");
        }
    }
}
