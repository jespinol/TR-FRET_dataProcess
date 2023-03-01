import localsolver.*;

import java.io.File;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Locale;
import java.util.Scanner;

public class CurveFitting {
    // Number of observations
    private int nbObservations;

    // Inputs and outputs
    private double[] inputs;
    private double[] outputs;

    // LocalSolver
    private final LocalSolver localsolver;

    // Decision variables
    private LSExpression a, b, c, d;

    // Objective
    private LSExpression squareError;

    private HashMap<Integer, ArrayList<Float>> instanceData;

    private boolean areThereStats;

    CurveFitting(LocalSolver localsolver, HashMap<Integer, ArrayList<Float>> instanceData, boolean areThereStats) {
        this.localsolver = localsolver;
        this.instanceData = instanceData;
        this.areThereStats = areThereStats;
    }

    // Read instance data

    private void readInstance(String fileName) throws IOException {
        try (Scanner input = new Scanner(new File(fileName))) {
            input.useLocale(Locale.ROOT);

            nbObservations = input.nextInt();

            inputs = new double[nbObservations];
            outputs = new double[nbObservations];
            for (int i = 0; i < nbObservations; ++i) {
                inputs[i] = input.nextDouble();
                outputs[i] = input.nextDouble();
            }
        }
    }
    private void readInstance() {
        int signalKey = areThereStats ? instanceData.size() - 2 : instanceData.size() - 1;
        nbObservations = instanceData.get(0).size();
        inputs = new double[nbObservations];
        outputs = new double[nbObservations];
        for (int i = 2; i < nbObservations; ++i) {
            inputs[i] = instanceData.get(0).get(i);
            outputs[i] = instanceData.get(signalKey).get(i);
        }
    }


    private void solve(int limit) {
        // Declare the optimization model
        LSModel model = localsolver.getModel();

        // Decision variables (parameters of the mapping function)
        a = model.floatVar(-1000, 10000);
        b = model.floatVar(-100, 100);
        c = model.floatVar(-100, 100);
        d = model.floatVar(-100, 100);

        // Minimize square error between prediction and output
        squareError = model.sum();
        for (int i = 0; i < nbObservations; ++i) {
//            LSExpression prediction = model.sum(model.prod(a, model.sin(model.sub(b, inputs[i]))),
//                    model.prod(c, Math.pow(inputs[i], 2)), d);
            LSExpression prediction = model.div(inputs[i],model.sum(inputs[i],a));
            LSExpression error = model.pow(model.sub(prediction, outputs[i]), 2);
            System.out.println(a);
            System.out.println(prediction);
            System.out.println(outputs[i]);
            squareError.addOperand(error);

        }

        model.minimize(squareError);
        model.close();

        // Parameterize the solver
        localsolver.getParam().setTimeLimit(limit);

        localsolver.solve();
    }

    /* Write the solution in a file */
    private void writeSolution(String fileName) throws IOException {
        try (PrintWriter output = new PrintWriter(fileName)) {
            output.println("Optimal mapping function");
            output.println("a = " + a.getDoubleValue());
//            output.println("b = " + b.getDoubleValue());
//            output.println("c = " + c.getDoubleValue());
//            output.println("d = " + d.getDoubleValue());
        }
    }
    private void printSolution() {
        System.out.println("\n------------------------------ KD estimate ------------------------------");
        System.out.println("KD " + a.getDoubleValue());
//        System.out.println(b.getDoubleValue());
//        System.out.println(c.getDoubleValue());
//        System.out.println(d.getDoubleValue());
    }

    private void printStats() {
        System.out.println("\n------------------------------- Fit stats -------------------------------");
        System.out.println("SSE " + squareError.getDoubleValue());
        double alpha = 0.05;
        double df = 3;
//        ChiSquaredDistribution x2 = new ChiSquaredDistribution( df );
    }

    void runSolver() {
        CurveFitting model = new CurveFitting(localsolver, instanceData, areThereStats);
        model.readInstance();
        model.solve(100);
        model.printSolution();
        model.printStats();
    }

    public static void main(String[] args) throws IOException {
//        if (args.length < 1) {
//            System.err.println("Usage: java CurveFitting inputFile [outputFile] [timeLimit]");
//            System.exit(1);
//        }
//        String instanceFile = args[0];
//        String outputFile = args.length > 1 ? args[1] : null;
//        String strTimeLimit = args.length > 2 ? args[2] : "3";
//
//        try (LocalSolver localsolver = new LocalSolver()) {
//            CurveFitting model = new CurveFitting(localsolver);
//            model.readInstance(instanceFile);
//            model.solve(Integer.parseInt(strTimeLimit));
//            if (outputFile != null) {
//                model.writeSolution(outputFile);
//            }
//        } catch (Exception ex) {
//            System.err.println(ex);
//            ex.printStackTrace();
//            System.exit(1);
//        }
    }
}

